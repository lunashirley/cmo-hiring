"""LLM client supporting Ollama and Anthropic Claude API."""
import json
import os
import time
import httpx
from sqlalchemy.ext.asyncio import AsyncSession

TIMEOUT = 180.0


async def chat(
    messages: list[dict],
    model: str,
    endpoint: str,
    session: AsyncSession | None = None,
    run_id: str | None = None,
    agent: str | None = None,
    attempt: int = 1,
    provider: str = "ollama",
    api_key: str = "",
) -> tuple[str, int, int]:
    """Call LLM. Returns (response_text, token_in, token_out)."""
    if provider == "anthropic":
        return await _chat_anthropic(messages, model, api_key, session, run_id, agent, attempt)
    return await _chat_ollama(messages, model, endpoint, session, run_id, agent, attempt)


async def _chat_ollama(
    messages: list[dict],
    model: str,
    endpoint: str,
    session: AsyncSession | None,
    run_id: str | None,
    agent: str | None,
    attempt: int,
) -> tuple[str, int, int]:
    from modules.learning import log_event

    url = endpoint.rstrip("/") + "/api/chat"
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {"temperature": 0.7},
    }

    t0 = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:
        if session and run_id and agent:
            await log_event(session, run_id=run_id, agent=agent, event="error",
                            attempt=attempt, notes=str(exc))
        raise

    elapsed_ms = int((time.monotonic() - t0) * 1000)
    text = data.get("message", {}).get("content", "")
    token_in = data.get("prompt_eval_count", 0)
    token_out = data.get("eval_count", 0)

    if session and run_id and agent:
        await log_event(session, run_id=run_id, agent=agent, event="response",
                        attempt=attempt, duration_ms=elapsed_ms,
                        token_in=token_in, token_out=token_out)

    return text, token_in, token_out


async def _chat_anthropic(
    messages: list[dict],
    model: str,
    api_key: str,
    session: AsyncSession | None,
    run_id: str | None,
    agent: str | None,
    attempt: int,
) -> tuple[str, int, int]:
    from modules.learning import log_event
    from anthropic import AsyncAnthropic

    key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
    if not key:
        raise ValueError("Anthropic API key not configured. Set it in Settings or the ANTHROPIC_API_KEY env var.")

    system_content = ""
    user_messages = []
    for msg in messages:
        if msg["role"] == "system":
            system_content = msg["content"]
        else:
            user_messages.append({"role": msg["role"], "content": msg["content"]})

    if not user_messages:
        user_messages = [{"role": "user", "content": system_content}]
        system_content = ""

    client = AsyncAnthropic(api_key=key)
    kwargs: dict = {
        "model": model,
        "max_tokens": 4096,
        "messages": user_messages,
    }
    if system_content:
        kwargs["system"] = system_content

    t0 = time.monotonic()
    try:
        response = await client.messages.create(**kwargs)
    except Exception as exc:
        if session and run_id and agent:
            await log_event(session, run_id=run_id, agent=agent, event="error",
                            attempt=attempt, notes=str(exc))
        raise

    elapsed_ms = int((time.monotonic() - t0) * 1000)
    text = response.content[0].text if response.content else ""
    token_in = response.usage.input_tokens
    token_out = response.usage.output_tokens

    if session and run_id and agent:
        await log_event(session, run_id=run_id, agent=agent, event="response",
                        attempt=attempt, duration_ms=elapsed_ms,
                        token_in=token_in, token_out=token_out)

    return text, token_in, token_out


def extract_json(text: str) -> dict | list:
    """Strip markdown fences and parse JSON from LLM response."""
    text = text.strip()
    # Strip <think>...</think> blocks (deepseek-r1 style)
    import re
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    return json.loads(text)
