"""
Module B — Agent Orchestration.
Runs specialist agents in parallel, then HoC QA with retry loop.
Streams progress via asyncio.Queue → SSE.
"""
import asyncio
import json
import re
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

import llm
import agent_loader
from models import Atom, Output, QAResult, Setting, Run
from modules.learning import log_event, get_exemplars
from ulid import ULID

PLATFORMS = ["linkedin", "x_twitter", "newsletter", "video_script"]


async def _get_setting(session: AsyncSession, key: str, default: str) -> str:
    row = await session.get(Setting, key)
    return row.value if row else default


def _build_messages(agent_body: str, context: dict) -> list[dict]:
    """Fill placeholders and split into system/user messages."""
    prompt_section = agent_loader.extract_prompt_section(agent_body)
    for k, v in context.items():
        prompt_section = prompt_section.replace(f"{{{{{k}}}}}", v)

    # Strip unused optional blocks
    prompt_section = re.sub(r"\{%.*?%\}.*?\{%.*?%\}", "", prompt_section, flags=re.DOTALL)

    system_match = re.search(r"SYSTEM:\s*\n(.*?)(?=USER:)", prompt_section, re.DOTALL)
    user_match = re.search(r"USER:\s*\n(.*)", prompt_section, re.DOTALL)

    system = system_match.group(1).strip() if system_match else ""
    user = user_match.group(1).strip() if user_match else prompt_section

    msgs = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.append({"role": "user", "content": user})
    return msgs


async def _run_specialist(
    session: AsyncSession,
    run_id: str,
    platform: str,
    atoms: list[dict],
    brand_voice_content: str,
    model: str,
    endpoint: str,
    exemplars: list[dict],
    rework_notes: dict | None,
    attempt: int,
    provider: str = "ollama",
    api_key: str = "",
) -> str:
    """Call one specialist agent. Returns raw JSON response text."""
    agent = agent_loader.load_agent(platform)
    template = agent_loader.load_template(platform)

    context = {
        "brand_voice": brand_voice_content,
        "atoms_json": json.dumps(atoms, indent=2),
        "template": template["body"],
        "exemplars_json": json.dumps(exemplars, indent=2) if exemplars else "",
        "rework_notes_json": json.dumps(rework_notes, indent=2) if rework_notes else "",
    }

    messages = _build_messages(agent["body"], context)
    await log_event(session, run_id=run_id, agent=platform, event="start" if attempt == 1 else "retry",
                    attempt=attempt)

    text, t_in, t_out = await llm.chat(
        messages, model=model, endpoint=endpoint,
        session=session, run_id=run_id, agent=platform, attempt=attempt,
        provider=provider, api_key=api_key,
    )
    return text, agent["version"], template["version"]


async def _run_hoc(
    session: AsyncSession,
    run_id: str,
    platform: str,
    content: str,
    atoms: list[dict],
    brand_voice_content: str,
    model: str,
    endpoint: str,
    attempt: int,
    provider: str = "ollama",
    api_key: str = "",
) -> dict:
    """Run Head of Content QA. Returns verdict dict."""
    agent = agent_loader.load_agent("head_of_content")
    template = agent_loader.load_template(platform)

    context = {
        "platform": platform,
        "brand_voice": brand_voice_content,
        "template": template["body"],
        "content_output": content,
        "atoms_json": json.dumps(atoms, indent=2),
    }

    messages = _build_messages(agent["body"], context)
    await log_event(session, run_id=run_id, agent="hoc", event="start", attempt=attempt)

    text, _, _ = await llm.chat(
        messages, model=model, endpoint=endpoint,
        session=session, run_id=run_id, agent="hoc", attempt=attempt,
        provider=provider, api_key=api_key,
    )
    try:
        verdict = llm.extract_json(text)
        if not isinstance(verdict, dict):
            raise ValueError("HoC returned non-dict")
        return verdict
    except Exception:
        return {"verdict": "fail", "rubric": {}, "summary": f"HoC JSON parse error: {text[:200]}"}


async def _process_platform(
    session: AsyncSession,
    run_id: str,
    platform: str,
    atoms: list[dict],
    brand_voice_content: str,
    brand_voice_slug: str,
    model: str,
    endpoint: str,
    max_attempts: int,
    progress_queue: asyncio.Queue,
    provider: str = "ollama",
    api_key: str = "",
) -> dict:
    """Full lifecycle for one platform: specialist → HoC → retry. Returns output dict."""
    exemplars = await get_exemplars(session, platform, brand_voice_slug, n=3)
    rework_notes = None
    approved_content = None
    agent_version = template_version = 1
    qa_result = None
    content = ""
    metadata = {}

    for attempt in range(1, max_attempts + 1):
        await progress_queue.put({"type": "platform_start", "platform": platform, "attempt": attempt})

        # Specialist
        try:
            raw_text, agent_version, template_version = await _run_specialist(
                session, run_id, platform, atoms, brand_voice_content,
                model, endpoint, exemplars, rework_notes, attempt,
                provider=provider, api_key=api_key,
            )
            try:
                specialist_result = llm.extract_json(raw_text)
                if isinstance(specialist_result, dict):
                    content = specialist_result.get("output", raw_text)
                    metadata = specialist_result.get("metadata", {})
                else:
                    content = raw_text
                    metadata = {}
            except Exception:
                content = raw_text
                metadata = {}
        except Exception as exc:
            await progress_queue.put({"type": "platform_error", "platform": platform, "error": str(exc)})
            await log_event(session, run_id=run_id, agent=platform, event="error",
                            attempt=attempt, notes=str(exc))
            if attempt < max_attempts:
                continue
            break

        # HoC QA
        await progress_queue.put({"type": "hoc_start", "platform": platform, "attempt": attempt})
        qa_result = await _run_hoc(
            session, run_id, platform, content, atoms,
            brand_voice_content, model, endpoint, attempt,
            provider=provider, api_key=api_key,
        )

        # Persist QA result
        qa_row = QAResult(
            id=f"qa_{ULID()}",
            output_id=f"output_{ULID()}",  # placeholder; updated below
            attempt=attempt,
            verdict=qa_result.get("verdict", "fail"),
            rubric_json=json.dumps(qa_result.get("rubric", {})),
            summary=qa_result.get("summary", ""),
            created_at=datetime.utcnow(),
        )

        if qa_result.get("verdict") == "pass":
            approved_content = content
            await log_event(session, run_id=run_id, agent="hoc", event="pass", attempt=attempt)
            await progress_queue.put({"type": "hoc_pass", "platform": platform, "attempt": attempt})
            break
        else:
            await log_event(session, run_id=run_id, agent="hoc", event="fail", attempt=attempt,
                            notes=qa_result.get("summary", ""))
            await progress_queue.put({"type": "hoc_fail", "platform": platform, "attempt": attempt,
                                      "summary": qa_result.get("summary", "")})
            rework_notes = qa_result.get("rubric", {})

    # Determine final status
    status = "approved" if approved_content else "escalated"
    final_content = approved_content or content  # content from last attempt

    output_id = f"output_{ULID()}"
    output = Output(
        id=output_id,
        run_id=run_id,
        platform=platform,
        version=1,
        content=final_content,
        metadata_json=json.dumps(metadata) if 'metadata' in dir() else "{}",
        status=status,
        agent_version=agent_version,
        template_version=template_version,
        qa_attempts=min(max_attempts, attempt if 'attempt' in dir() else 1),
        created_at=datetime.utcnow(),
    )
    session.add(output)
    await session.commit()

    await progress_queue.put({"type": "platform_done", "platform": platform, "status": status,
                              "output_id": output_id})
    return {"platform": platform, "output_id": output_id, "status": status, "content": final_content}


async def run_generation(
    session: AsyncSession,
    run_id: str,
    brand_voice_slug: str,
    model: str,
    endpoint: str,
    max_concurrency: int,
    max_attempts: int,
    progress_queue: asyncio.Queue,
    provider: str = "ollama",
    api_key: str = "",
) -> list[dict]:
    """
    Fan out all platforms in parallel (bounded by semaphore).
    Returns list of output dicts.
    """
    # Load approved atoms
    result = await session.execute(
        select(Atom).where(Atom.run_id == run_id).where(Atom.approved == True)
        .order_by(Atom.priority)
    )
    atoms_rows = result.scalars().all()
    atoms = [
        {
            "id": a.id,
            "type": a.type,
            "text": a.edited_text or a.text,
            "proposed_angle": a.proposed_angle,
            "confidence": a.confidence,
            "origin": a.origin,
            "priority": a.priority,
        }
        for a in atoms_rows
    ]

    # Load brand voice
    bv = agent_loader.load_brand_voice(brand_voice_slug)
    if not bv:
        raise ValueError(f"Brand voice '{brand_voice_slug}' not found")
    brand_voice_content = bv["content"]

    outputs = []
    for platform in PLATFORMS:
        from database import SessionLocal
        async with SessionLocal() as platform_session:
            try:
                result = await _process_platform(
                    platform_session, run_id, platform, atoms, brand_voice_content,
                    brand_voice_slug, model, endpoint, max_attempts, progress_queue,
                    provider=provider, api_key=api_key,
                )
                outputs.append(result)
            except Exception as exc:
                await progress_queue.put({"type": "platform_error", "platform": platform, "error": str(exc)})

    await progress_queue.put({"type": "done", "output_count": len(outputs)})
    return outputs
