"""
Module A — Atom extraction.
Runs the atom_extractor agent against normalized article text.
"""
import json
import re
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

import llm
import agent_loader
from models import Atom, Run, Setting
from modules.learning import log_event


async def _get_setting(session: AsyncSession, key: str, default: str) -> str:
    row = await session.get(Setting, key)
    return row.value if row else default


_CONFIDENCE_LABELS = {"low": 0.25, "medium": 0.5, "med": 0.5, "high": 0.85, "very high": 0.95}

def _parse_confidence(value) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return _CONFIDENCE_LABELS.get(str(value).strip().lower(), 0.5)


async def extract_atoms(
    session: AsyncSession,
    run_id: str,
    normalized_text: str,
    model: str,
    endpoint: str,
    provider: str = "ollama",
    api_key: str = "",
) -> list[dict]:
    """
    Run atom extraction. Returns list of atom dicts.
    Stores atoms in DB. Updates run status.
    """
    atom_min = await _get_setting(session, "atom_target_min", "8")
    atom_max = await _get_setting(session, "atom_target_max", "15")

    agent = agent_loader.load_agent("atom_extractor")
    prompt_body = agent_loader.extract_prompt_section(agent["body"])

    # Fill placeholders
    prompt_body = prompt_body.replace("{{atom_target_min}}", atom_min)
    prompt_body = prompt_body.replace("{{atom_target_max}}", atom_max)

    # Split SYSTEM / USER sections
    system_match = re.search(r"SYSTEM:\s*\n(.*?)(?=USER:)", prompt_body, re.DOTALL)
    user_match = re.search(r"USER:\s*\n(.*)", prompt_body, re.DOTALL)

    system_prompt = system_match.group(1).strip() if system_match else "You are a content atom extractor. Return JSON only."
    user_prompt_template = user_match.group(1).strip() if user_match else prompt_body

    user_prompt = user_prompt_template.replace("{{article_text}}", normalized_text)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    await log_event(session, run_id=run_id, agent="extractor", event="start", attempt=1)

    max_attempts = 2
    for attempt in range(1, max_attempts + 1):
        try:
            text, t_in, t_out = await llm.chat(
                messages, model=model, endpoint=endpoint,
                session=session, run_id=run_id, agent="extractor", attempt=attempt,
                provider=provider, api_key=api_key,
            )
            raw_atoms = llm.extract_json(text)
            if isinstance(raw_atoms, dict) and "atoms" in raw_atoms:
                raw_atoms = raw_atoms["atoms"]
            if not isinstance(raw_atoms, list):
                raise ValueError("Expected a JSON array")
            break
        except Exception as exc:
            if attempt == max_attempts:
                await log_event(session, run_id=run_id, agent="extractor", event="error",
                                attempt=attempt, notes=f"Extraction failed: {exc}")
                raise RuntimeError(f"Atom extraction failed: {exc}") from exc
            # Retry nudge
            messages.append({"role": "assistant", "content": text if 'text' in dir() else ""})
            messages.append({"role": "user", "content": "Return valid JSON array only. No markdown, no explanation."})

    # Persist atoms
    atoms_out = []
    for i, raw in enumerate(raw_atoms):
        offset = raw.get("source_offset", {})
        atom = Atom(
            id=f"atom_{run_id}_{i+1:03d}",
            run_id=run_id,
            type=raw.get("type", "insight"),
            text=raw.get("text", ""),
            source_offset_start=offset.get("start", 0) if isinstance(offset, dict) else 0,
            source_offset_end=offset.get("end", 0) if isinstance(offset, dict) else 0,
            proposed_angle=raw.get("proposed_angle", ""),
            confidence=_parse_confidence(raw.get("confidence", 0.5)),
            origin="extracted",
            priority=raw.get("priority", i + 1),
            approved=False,
        )
        session.add(atom)
        atoms_out.append({
            "id": atom.id,
            "type": atom.type,
            "text": atom.text,
            "proposed_angle": atom.proposed_angle,
            "confidence": atom.confidence,
            "origin": atom.origin,
            "priority": atom.priority,
            "approved": atom.approved,
        })

    await log_event(session, run_id=run_id, agent="extractor", event="pass",
                    notes=f"Extracted {len(atoms_out)} atoms")
    await session.commit()
    return atoms_out
