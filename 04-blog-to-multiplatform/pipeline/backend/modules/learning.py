"""
Module C — Learning & Observability.
Handles logging, ratings, exemplar pool, and versioning.
"""
import json
import difflib
import hashlib
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, case

from models import (
    Log, PayloadBlob, Rating, Output, OutputEdit,
    AgentVersion, TemplateVersion,
)


# ── Logging ──────────────────────────────────────────────────────────────────

async def log_event(
    session: AsyncSession,
    *,
    run_id: str | None = None,
    agent: str,
    event: str,
    attempt: int = 1,
    duration_ms: int = 0,
    token_in: int = 0,
    token_out: int = 0,
    payload: str | None = None,
    notes: str | None = None,
) -> None:
    payload_ref = None
    if payload:
        h = hashlib.sha256(payload.encode()).hexdigest()
        existing = await session.get(PayloadBlob, h)
        if not existing:
            session.add(PayloadBlob(sha256=h, content=payload))
        payload_ref = h

    entry = Log(
        ts=datetime.utcnow(),
        run_id=run_id,
        agent=agent,
        event=event,
        attempt=attempt,
        duration_ms=duration_ms,
        token_in=token_in,
        token_out=token_out,
        payload_ref=payload_ref,
        notes=notes,
    )
    session.add(entry)
    await session.flush()


async def get_logs(
    session: AsyncSession,
    run_id: str | None = None,
    agent: str | None = None,
    event: str | None = None,
    limit: int = 200,
    offset: int = 0,
) -> list[dict]:
    q = select(Log).order_by(desc(Log.ts))
    if run_id:
        q = q.where(Log.run_id == run_id)
    if agent:
        q = q.where(Log.agent == agent)
    if event:
        q = q.where(Log.event == event)
    q = q.limit(limit).offset(offset)
    result = await session.execute(q)
    return [_log_to_dict(r) for r in result.scalars()]


def _log_to_dict(log: Log) -> dict:
    return {
        "id": log.id,
        "ts": log.ts.isoformat(),
        "run_id": log.run_id,
        "agent": log.agent,
        "event": log.event,
        "attempt": log.attempt,
        "duration_ms": log.duration_ms,
        "token_in": log.token_in,
        "token_out": log.token_out,
        "notes": log.notes,
    }


async def get_agent_scorecards(session: AsyncSession) -> list[dict]:
    """Per-agent: call count, avg duration, retry rate, pass rate."""
    result = await session.execute(
        select(Log.agent,
               func.count(Log.id).label("calls"),
               func.avg(Log.duration_ms).label("avg_ms"),
               func.sum(case((Log.event == "retry", 1), else_=0)).label("retries"),
               func.sum(case((Log.event == "pass", 1), else_=0)).label("passes"),
               func.sum(case((Log.event == "fail", 1), else_=0)).label("fails"),
               ).group_by(Log.agent)
    )
    rows = result.all()
    return [
        {
            "agent": r.agent,
            "calls": r.calls,
            "avg_ms": int(r.avg_ms or 0),
            "retry_rate": round(r.retries / max(r.calls, 1), 3),
            "pass_rate": round(r.passes / max(r.passes + r.fails, 1), 3),
        }
        for r in rows
    ]


# ── Ratings ──────────────────────────────────────────────────────────────────

async def rate_output(
    session: AsyncSession,
    output_id: str,
    score: int,
    tags: list[str],
    note: str | None,
) -> dict:
    output = await session.get(Output, output_id)
    if not output:
        raise ValueError(f"Output {output_id} not found")

    from ulid import ULID
    rating = Rating(
        id=f"rating_{ULID()}",
        output_id=output_id,
        platform=output.platform,
        brand_voice_slug=output.run_id,  # filled properly via join in the route
        score=score,
        tags_json=json.dumps(tags),
        note=note,
        rated_at=datetime.utcnow(),
    )
    session.add(rating)
    await session.commit()
    return {"id": rating.id, "output_id": output_id, "score": score, "tags": tags}


async def get_ratings_summary(session: AsyncSession) -> list[dict]:
    result = await session.execute(
        select(Rating.platform,
               func.avg(Rating.score).label("avg_score"),
               func.count(Rating.id).label("count"),
               ).group_by(Rating.platform)
    )
    return [{"platform": r.platform, "avg_score": round(r.avg_score, 2), "count": r.count}
            for r in result.all()]


# ── Exemplar pool ─────────────────────────────────────────────────────────────

async def get_exemplars(
    session: AsyncSession,
    platform: str,
    brand_voice_slug: str,
    n: int = 3,
) -> list[dict]:
    """
    Top-N outputs for this (platform, brand_voice) pair by rating score,
    recency-weighted. Edited versions take precedence.
    """
    result = await session.execute(
        select(Output, Rating)
        .join(Rating, Rating.output_id == Output.id)
        .where(Output.platform == platform)
        .where(Output.status.in_(["approved", "final", "edited"]))
        .order_by(desc(Rating.score), desc(Rating.rated_at))
        .limit(n * 2)
    )
    rows = result.all()

    exemplars = []
    seen_ids = set()
    for output, rating in rows:
        if output.id in seen_ids:
            continue
        seen_ids.add(output.id)
        # Prefer edited content
        edits_result = await session.execute(
            select(OutputEdit).where(OutputEdit.output_id == output.id)
            .order_by(desc(OutputEdit.edited_at)).limit(1)
        )
        edit = edits_result.scalar_one_or_none()
        content = edit.edited_content if edit else output.content
        tags = json.loads(rating.tags_json) if rating.tags_json else []
        exemplars.append({
            "content": content,
            "score": rating.score,
            "tags": tags,
        })
        if len(exemplars) >= n:
            break
    return exemplars


# ── Output editing (diff capture) ──────────────────────────────────────────

async def save_output_edit(
    session: AsyncSession,
    output_id: str,
    new_content: str,
) -> dict:
    output = await session.get(Output, output_id)
    if not output:
        raise ValueError(f"Output {output_id} not found")

    diff = "\n".join(difflib.unified_diff(
        output.content.splitlines(),
        new_content.splitlines(),
        fromfile="original",
        tofile="edited",
        lineterm="",
    ))

    from ulid import ULID
    edit = OutputEdit(
        id=f"edit_{ULID()}",
        output_id=output_id,
        diff=diff,
        edited_content=new_content,
        edited_at=datetime.utcnow(),
    )
    session.add(edit)
    output.content = new_content
    output.status = "edited"
    await session.commit()
    return {"id": edit.id, "diff": diff}


# ── Versioning ────────────────────────────────────────────────────────────────

async def snapshot_agent(session: AsyncSession, agent_name: str, content: str, version: int) -> None:
    session.add(AgentVersion(agent=agent_name, version=version, content_md=content,
                             created_at=datetime.utcnow()))
    await session.flush()


async def snapshot_template(session: AsyncSession, platform: str, content: str, version: int) -> None:
    session.add(TemplateVersion(platform=platform, version=version, content_md=content,
                                created_at=datetime.utcnow()))
    await session.flush()


async def get_agent_history(session: AsyncSession, agent_name: str) -> list[dict]:
    result = await session.execute(
        select(AgentVersion).where(AgentVersion.agent == agent_name)
        .order_by(desc(AgentVersion.created_at))
    )
    return [{"version": r.version, "created_at": r.created_at.isoformat(), "content": r.content_md}
            for r in result.scalars()]
