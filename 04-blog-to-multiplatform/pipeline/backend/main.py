"""
Content Repurposing Pipeline — FastAPI backend
"""
import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Annotated, AsyncGenerator

from dotenv import load_dotenv
from fastapi import (
    Cookie, Depends, FastAPI, HTTPException, Request, Response, status,
)
from sqlalchemy import text
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, PlainTextResponse
from pydantic import BaseModel
from sqlalchemy import select, desc, delete
from sqlalchemy.ext.asyncio import AsyncSession
from ulid import ULID

load_dotenv()

from database import get_db, init_db, engine
from models import (
    Atom, BrandVoice, Log, Output, OutputEdit, QAResult,
    Rating, Run, Setting, User,
)
from auth import hash_password, verify_password, create_token, require_auth
from config import DEFAULT_SETTINGS, OUTPUT_DIR, get_pipeline_password
import agent_loader
from modules.learning import (
    log_event, get_logs, get_agent_scorecards,
    rate_output, get_ratings_summary,
    save_output_edit, snapshot_agent, snapshot_template, get_agent_history,
)
from modules.ingestion import ingest
from modules.extraction import extract_atoms
from modules.orchestration import run_generation

app = FastAPI(title="Content Repurposing Pipeline")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    await init_db()
    async with engine.begin() as conn:
        await conn.execute(text("PRAGMA journal_mode=WAL"))
        await conn.execute(text("PRAGMA synchronous=NORMAL"))
    async with __import__("database").SessionLocal() as session:
        # Seed default settings
        for key, value in DEFAULT_SETTINGS.items():
            if not await session.get(Setting, key):
                session.add(Setting(key=key, value=value))
        # Seed default user
        existing = await session.execute(select(User).where(User.username == "admin"))
        if not existing.scalar_one_or_none():
            session.add(User(
                username="admin",
                password_hash=hash_password(get_pipeline_password()),
            ))
        await session.commit()


# ── Auth ──────────────────────────────────────────────────────────────────────

class LoginPayload(BaseModel):
    password: str


@app.post("/api/auth/login")
async def login(payload: LoginPayload, response: Response, db: AsyncSession = Depends(get_db)):
    user = (await db.execute(select(User).where(User.username == "admin"))).scalar_one_or_none()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid password")
    token = create_token("admin")
    response.set_cookie("access_token", token, httponly=True, samesite="lax", max_age=604800)
    return {"ok": True}


@app.post("/api/auth/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    return {"ok": True}


@app.get("/api/auth/me")
async def me(username: str = Depends(require_auth)):
    return {"username": username}


# ── Settings ──────────────────────────────────────────────────────────────────

@app.get("/api/settings")
async def get_settings(db: AsyncSession = Depends(get_db), _: str = Depends(require_auth)):
    rows = (await db.execute(select(Setting))).scalars().all()
    return {r.key: r.value for r in rows}


class SettingsUpdate(BaseModel):
    settings: dict[str, str]


@app.put("/api/settings")
async def update_settings(payload: SettingsUpdate, db: AsyncSession = Depends(get_db),
                          _: str = Depends(require_auth)):
    for k, v in payload.settings.items():
        row = await db.get(Setting, k)
        if row:
            row.value = v
        else:
            db.add(Setting(key=k, value=v))
    await db.commit()
    return {"ok": True}


# ── Runs ──────────────────────────────────────────────────────────────────────

class RunCreate(BaseModel):
    url: str | None = None
    pasted_text: str | None = None


@app.post("/api/runs")
async def create_run(payload: RunCreate, db: AsyncSession = Depends(get_db),
                     _: str = Depends(require_auth)):
    if not payload.url and not payload.pasted_text:
        raise HTTPException(status_code=400, detail="Provide url or pasted_text")

    run_id = f"run_{ULID()}"
    run = Run(id=run_id, url=payload.url, source_type="url" if payload.url else "paste",
              status="ingesting", created_at=datetime.utcnow())
    db.add(run)
    await db.commit()

    # Ingest in background
    asyncio.create_task(_ingest_task(run_id, payload.url, payload.pasted_text))
    return {"run_id": run_id, "status": "ingesting"}


async def _ingest_task(run_id: str, url: str | None, pasted: str | None):
    from database import SessionLocal
    async with SessionLocal() as session:
        run = await session.get(Run, run_id)
        try:
            result = await ingest(url=url, pasted_text=pasted)
            run.raw_content = result.raw[:50000]
            run.normalized_content = result.normalized[:50000]
            run.source_type = result.source_type
            run.status = "extracting"
            await session.commit()

            settings = {r.key: r.value for r in (await session.execute(select(Setting))).scalars()}
            await extract_atoms(
                session, run_id, result.normalized,
                model=settings.get("model", "deepseek-r1:8b"),
                endpoint=settings.get("ollama_endpoint", "http://localhost:11434"),
                provider=settings.get("provider", "ollama"),
                api_key=settings.get("anthropic_api_key", ""),
            )
            run = await session.get(Run, run_id)
            run.status = "hitl"
            await session.commit()
        except Exception as exc:
            run = await session.get(Run, run_id)
            run.status = "error"
            run.error_msg = str(exc)[:1000]
            await session.commit()


@app.get("/api/runs")
async def list_runs(db: AsyncSession = Depends(get_db), _: str = Depends(require_auth)):
    result = await db.execute(select(Run).order_by(desc(Run.created_at)).limit(50))
    runs = result.scalars().all()
    return [_run_to_dict(r) for r in runs]


@app.delete("/api/runs/{run_id}")
async def delete_run(run_id: str, db: AsyncSession = Depends(get_db), _: str = Depends(require_auth)):
    run = await db.get(Run, run_id)
    if not run:
        raise HTTPException(404, "Run not found")
    output_ids = list((await db.execute(select(Output.id).where(Output.run_id == run_id))).scalars())
    if output_ids:
        await db.execute(delete(QAResult).where(QAResult.output_id.in_(output_ids)))
        await db.execute(delete(Rating).where(Rating.output_id.in_(output_ids)))
        await db.execute(delete(OutputEdit).where(OutputEdit.output_id.in_(output_ids)))
    await db.execute(delete(Output).where(Output.run_id == run_id))
    await db.execute(delete(Atom).where(Atom.run_id == run_id))
    await db.execute(delete(Log).where(Log.run_id == run_id))
    await db.delete(run)
    await db.commit()
    return {"ok": True}


@app.get("/api/runs/{run_id}")
async def get_run(run_id: str, db: AsyncSession = Depends(get_db), _: str = Depends(require_auth)):
    run = await db.get(Run, run_id)
    if not run:
        raise HTTPException(404, "Run not found")
    return _run_to_dict(run)


def _run_to_dict(run: Run) -> dict:
    return {
        "id": run.id,
        "url": run.url,
        "source_type": run.source_type,
        "status": run.status,
        "brand_voice_slug": run.brand_voice_slug,
        "created_at": run.created_at.isoformat(),
        "error_msg": run.error_msg,
    }


# ── Atoms ─────────────────────────────────────────────────────────────────────

@app.get("/api/runs/{run_id}/atoms")
async def get_atoms(run_id: str, db: AsyncSession = Depends(get_db), _: str = Depends(require_auth)):
    result = await db.execute(
        select(Atom).where(Atom.run_id == run_id).order_by(Atom.priority)
    )
    return [_atom_to_dict(a) for a in result.scalars()]


class AtomUpdate(BaseModel):
    text: str | None = None
    type: str | None = None
    proposed_angle: str | None = None
    approved: bool | None = None
    priority: int | None = None


@app.put("/api/runs/{run_id}/atoms/{atom_id}")
async def update_atom(run_id: str, atom_id: str, payload: AtomUpdate,
                      db: AsyncSession = Depends(get_db), _: str = Depends(require_auth)):
    atom = await db.get(Atom, atom_id)
    if not atom or atom.run_id != run_id:
        raise HTTPException(404, "Atom not found")
    if payload.text is not None:
        atom.edited_text = payload.text
    if payload.type is not None:
        atom.type = payload.type
    if payload.proposed_angle is not None:
        atom.proposed_angle = payload.proposed_angle
    if payload.approved is not None:
        atom.approved = payload.approved
    if payload.priority is not None:
        atom.priority = payload.priority
    await db.commit()
    return _atom_to_dict(atom)


class AtomCreate(BaseModel):
    type: str
    text: str
    proposed_angle: str = ""


@app.post("/api/runs/{run_id}/atoms")
async def add_atom(run_id: str, payload: AtomCreate, db: AsyncSession = Depends(get_db),
                   _: str = Depends(require_auth)):
    # Determine next priority
    result = await db.execute(
        select(Atom).where(Atom.run_id == run_id).order_by(desc(Atom.priority)).limit(1)
    )
    last = result.scalar_one_or_none()
    next_priority = (last.priority + 1) if last else 1

    atom = Atom(
        id=f"atom_{run_id}_{ULID()}",
        run_id=run_id,
        type=payload.type,
        text=payload.text,
        proposed_angle=payload.proposed_angle,
        confidence=1.0,
        origin="manual",
        priority=next_priority,
        approved=False,
    )
    db.add(atom)
    await db.commit()
    return _atom_to_dict(atom)


@app.delete("/api/runs/{run_id}/atoms/{atom_id}")
async def delete_atom(run_id: str, atom_id: str, db: AsyncSession = Depends(get_db),
                      _: str = Depends(require_auth)):
    atom = await db.get(Atom, atom_id)
    if not atom or atom.run_id != run_id:
        raise HTTPException(404, "Atom not found")
    await db.delete(atom)
    await db.commit()
    return {"ok": True}


class ReorderPayload(BaseModel):
    atom_ids: list[str]


@app.post("/api/runs/{run_id}/atoms/reorder")
async def reorder_atoms(run_id: str, payload: ReorderPayload, db: AsyncSession = Depends(get_db),
                        _: str = Depends(require_auth)):
    for i, atom_id in enumerate(payload.atom_ids):
        atom = await db.get(Atom, atom_id)
        if atom and atom.run_id == run_id:
            atom.priority = i + 1
    await db.commit()
    return {"ok": True}


class BrandVoiceSetPayload(BaseModel):
    brand_voice_slug: str


@app.post("/api/runs/{run_id}/brand-voice")
async def set_brand_voice(run_id: str, payload: BrandVoiceSetPayload,
                          db: AsyncSession = Depends(get_db), _: str = Depends(require_auth)):
    run = await db.get(Run, run_id)
    if not run:
        raise HTTPException(404, "Run not found")
    run.brand_voice_slug = payload.brand_voice_slug
    await db.commit()
    return {"ok": True}


@app.post("/api/runs/{run_id}/atoms/bulk-approve")
async def bulk_approve_atoms(run_id: str, db: AsyncSession = Depends(get_db),
                             _: str = Depends(require_auth)):
    result = await db.execute(select(Atom).where(Atom.run_id == run_id))
    for atom in result.scalars():
        atom.approved = True
    await db.commit()
    return {"ok": True}


def _atom_to_dict(a: Atom) -> dict:
    return {
        "id": a.id,
        "run_id": a.run_id,
        "type": a.type,
        "text": a.edited_text or a.text,
        "original_text": a.text,
        "is_edited": a.edited_text is not None,
        "proposed_angle": a.proposed_angle,
        "confidence": a.confidence,
        "origin": a.origin,
        "priority": a.priority,
        "approved": a.approved,
    }


# ── Generation (SSE) ──────────────────────────────────────────────────────────

# In-memory queue registry — keyed by run_id
_generation_queues: dict[str, asyncio.Queue] = {}


@app.post("/api/runs/{run_id}/generate/start")
async def start_generation(run_id: str, db: AsyncSession = Depends(get_db),
                           _: str = Depends(require_auth)):
    run = await db.get(Run, run_id)
    if not run:
        raise HTTPException(404, "Run not found")
    if not run.brand_voice_slug:
        raise HTTPException(400, "Select a brand voice before generating")

    approved_count = len(
        (await db.execute(select(Atom).where(Atom.run_id == run_id).where(Atom.approved == True)))
        .scalars().all()
    )
    if approved_count == 0:
        raise HTTPException(400, "Approve at least one atom before generating")

    settings = {r.key: r.value for r in (await db.execute(select(Setting))).scalars()}

    queue: asyncio.Queue = asyncio.Queue()
    _generation_queues[run_id] = queue

    run.status = "generating"
    await db.commit()

    asyncio.create_task(_generation_task(
        run_id=run_id,
        brand_voice_slug=run.brand_voice_slug,
        model=settings.get("model", "deepseek-r1:8b"),
        endpoint=settings.get("ollama_endpoint", "http://localhost:11434"),
        max_concurrency=int(settings.get("max_concurrency", "2")),
        max_attempts=int(settings.get("qa_max_attempts", "3")),
        queue=queue,
        provider=settings.get("provider", "ollama"),
        api_key=settings.get("anthropic_api_key", ""),
    ))

    return {"ok": True, "message": "Generation started — connect to /stream for progress"}


async def _generation_task(run_id, brand_voice_slug, model, endpoint, max_concurrency, max_attempts, queue, provider="ollama", api_key=""):
    from database import SessionLocal
    async with SessionLocal() as session:
        try:
            outputs = await run_generation(
                session, run_id, brand_voice_slug,
                model, endpoint, max_concurrency, max_attempts, queue,
                provider=provider, api_key=api_key,
            )
            run = await session.get(Run, run_id)
            if run:
                run.status = "done"
            await session.commit()
            # Export to output/ folder
            await _export_outputs(run_id, outputs, session)
        except Exception as exc:
            async with SessionLocal() as err_session:
                run = await err_session.get(Run, run_id)
                if run:
                    run.status = "error"
                    run.error_msg = str(exc)[:1000]
                await err_session.commit()
            await queue.put({"type": "error", "error": str(exc)})
        finally:
            await queue.put(None)  # sentinel


@app.get("/api/runs/{run_id}/generate/stream")
async def stream_generation(run_id: str, request: Request,
                            access_token: str | None = Cookie(default=None)):
    if not access_token:
        raise HTTPException(401, "Not authenticated")

    async def event_stream() -> AsyncGenerator[str, None]:
        queue = _generation_queues.get(run_id)
        if not queue:
            yield f"data: {json.dumps({'type': 'error', 'error': 'No active generation for this run'})}\n\n"
            return
        while True:
            if await request.is_disconnected():
                break
            try:
                event = await asyncio.wait_for(queue.get(), timeout=30.0)
            except asyncio.TimeoutError:
                yield "data: {\"type\":\"heartbeat\"}\n\n"
                continue
            if event is None:
                yield f"data: {json.dumps({'type': 'complete'})}\n\n"
                _generation_queues.pop(run_id, None)
                break
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


# ── Outputs ───────────────────────────────────────────────────────────────────

@app.get("/api/runs/{run_id}/outputs")
async def get_outputs(run_id: str, db: AsyncSession = Depends(get_db),
                      _: str = Depends(require_auth)):
    result = await db.execute(
        select(Output).where(Output.run_id == run_id).order_by(Output.created_at)
    )
    return [_output_to_dict(o) for o in result.scalars()]


@app.get("/api/outputs")
async def list_all_outputs(db: AsyncSession = Depends(get_db), _: str = Depends(require_auth)):
    result = await db.execute(select(Output).order_by(desc(Output.created_at)).limit(100))
    return [_output_to_dict(o) for o in result.scalars()]


class OutputEditPayload(BaseModel):
    content: str


@app.put("/api/outputs/{output_id}")
async def edit_output(output_id: str, payload: OutputEditPayload,
                      db: AsyncSession = Depends(get_db), _: str = Depends(require_auth)):
    result = await save_output_edit(db, output_id, payload.content)
    return result


@app.get("/api/outputs/{output_id}/export")
async def export_output(output_id: str, fmt: str = "md",
                        db: AsyncSession = Depends(get_db), _: str = Depends(require_auth)):
    output = await db.get(Output, output_id)
    if not output:
        raise HTTPException(404, "Output not found")
    filename = f"{output.run_id}_{output.platform}_v{output.version}.{fmt}"
    return PlainTextResponse(output.content, headers={
        "Content-Disposition": f'attachment; filename="{filename}"'
    })


def _output_to_dict(o: Output) -> dict:
    return {
        "id": o.id,
        "run_id": o.run_id,
        "platform": o.platform,
        "version": o.version,
        "content": o.content,
        "metadata": json.loads(o.metadata_json) if o.metadata_json else {},
        "status": o.status,
        "qa_attempts": o.qa_attempts,
        "created_at": o.created_at.isoformat(),
    }


# ── Ratings ───────────────────────────────────────────────────────────────────

class RatingPayload(BaseModel):
    score: int
    tags: list[str] = []
    note: str | None = None


@app.post("/api/outputs/{output_id}/rate")
async def rate(output_id: str, payload: RatingPayload, db: AsyncSession = Depends(get_db),
               _: str = Depends(require_auth)):
    if not 1 <= payload.score <= 5:
        raise HTTPException(400, "Score must be 1–5")
    result = await rate_output(db, output_id, payload.score, payload.tags, payload.note)
    return result


@app.get("/api/ratings")
async def ratings_summary(db: AsyncSession = Depends(get_db), _: str = Depends(require_auth)):
    return await get_ratings_summary(db)


# ── Brand Voices ──────────────────────────────────────────────────────────────

@app.get("/api/brand-voices")
async def list_bv(_: str = Depends(require_auth)):
    return agent_loader.list_brand_voices()


@app.get("/api/brand-voices/{slug}")
async def get_bv(slug: str, _: str = Depends(require_auth)):
    bv = agent_loader.load_brand_voice(slug)
    if not bv:
        raise HTTPException(404, "Brand voice not found")
    return bv


class BrandVoicePayload(BaseModel):
    slug: str
    content: str


@app.post("/api/brand-voices")
async def create_bv(payload: BrandVoicePayload, _: str = Depends(require_auth)):
    agent_loader.save_brand_voice(payload.slug, payload.content)
    return {"ok": True}


@app.put("/api/brand-voices/{slug}")
async def update_bv(slug: str, payload: BrandVoicePayload, db: AsyncSession = Depends(get_db),
                    _: str = Depends(require_auth)):
    existing = agent_loader.load_brand_voice(slug)
    if existing:
        await snapshot_agent(db, f"bv_{slug}", existing["content"], existing["version"])
        await db.commit()
    agent_loader.save_brand_voice(slug, payload.content)
    return {"ok": True}


# ── Agents ────────────────────────────────────────────────────────────────────

@app.get("/api/agents")
async def list_agents_route(_: str = Depends(require_auth)):
    return agent_loader.list_agents()


@app.get("/api/agents/{name}")
async def get_agent(name: str, _: str = Depends(require_auth)):
    try:
        return agent_loader.load_agent(name)
    except FileNotFoundError:
        raise HTTPException(404, "Agent not found")


class AgentUpdatePayload(BaseModel):
    content: str


@app.put("/api/agents/{name}")
async def update_agent(name: str, payload: AgentUpdatePayload, db: AsyncSession = Depends(get_db),
                       _: str = Depends(require_auth)):
    try:
        existing = agent_loader.load_agent(name)
        await snapshot_agent(db, name, existing["content"], existing["version"])
        await db.commit()
    except FileNotFoundError:
        pass
    agent_loader.save_agent(name, payload.content)
    return {"ok": True}


@app.get("/api/agents/{name}/history")
async def agent_history(name: str, db: AsyncSession = Depends(get_db), _: str = Depends(require_auth)):
    return await get_agent_history(db, name)


# ── Logs ──────────────────────────────────────────────────────────────────────

@app.get("/api/logs")
async def logs(run_id: str | None = None, agent: str | None = None, event: str | None = None,
               limit: int = 100, offset: int = 0,
               db: AsyncSession = Depends(get_db), _: str = Depends(require_auth)):
    return await get_logs(db, run_id=run_id, agent=agent, event=event, limit=limit, offset=offset)


@app.get("/api/logs/scorecards")
async def scorecards(db: AsyncSession = Depends(get_db), _: str = Depends(require_auth)):
    return await get_agent_scorecards(db)


# ── Export helpers ────────────────────────────────────────────────────────────

async def _export_outputs(run_id: str, outputs: list[dict], session: AsyncSession):
    """Write final outputs to /output/<run_id>/ folder."""
    run_dir = OUTPUT_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    # Write source metadata
    run = await session.get(Run, run_id)
    if run:
        meta = {"run_id": run_id, "url": run.url, "created_at": run.created_at.isoformat()}
        (run_dir / "source.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    for out in outputs:
        platform = out.get("platform", "unknown")
        content = out.get("content", "")
        (run_dir / f"{platform}.md").write_text(content, encoding="utf-8")
