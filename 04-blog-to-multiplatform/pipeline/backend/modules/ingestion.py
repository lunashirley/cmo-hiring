"""
Module A — Ingestion & content normalization.
Fetches via Jina Reader or accepts pasted text, normalizes, detects issues.
"""
import re
import httpx

JINA_BASE = "https://r.jina.ai/"
JINA_TIMEOUT = 20.0
JINA_RETRIES = 2
MIN_WORDS = 300


class IngestionResult:
    def __init__(
        self,
        raw: str,
        normalized: str,
        source_type: str,
        warnings: list[str] | None = None,
    ):
        self.raw = raw
        self.normalized = normalized
        self.source_type = source_type
        self.warnings = warnings or []


async def fetch_url(url: str) -> str:
    """Fetch article via Jina Reader with retries."""
    jina_url = JINA_BASE + url
    last_exc = None
    for attempt in range(1, JINA_RETRIES + 1):
        try:
            async with httpx.AsyncClient(timeout=JINA_TIMEOUT) as client:
                resp = await client.get(jina_url, headers={"Accept": "text/plain"})
                resp.raise_for_status()
                text = resp.text
                if len(text.strip()) < 100:
                    raise ValueError("Jina returned near-empty content")
                return text
        except Exception as exc:
            last_exc = exc
            if attempt < JINA_RETRIES:
                import asyncio
                await asyncio.sleep(2 ** attempt)
    raise RuntimeError(f"Jina Reader failed after {JINA_RETRIES} attempts: {last_exc}")


def normalize(text: str) -> str:
    """Strip boilerplate noise, deduplicate whitespace, preserve paragraph breaks."""
    # Remove common Jina/reader boilerplate patterns
    text = re.sub(r"(?m)^(Skip to|Jump to|Navigation|Cookie|Privacy Policy).*$", "", text)
    # Collapse 3+ blank lines to 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Collapse runs of spaces/tabs (but keep newlines)
    text = re.sub(r"[^\S\n]+", " ", text)
    # Strip leading/trailing whitespace per line
    lines = [l.rstrip() for l in text.splitlines()]
    return "\n".join(lines).strip()


def detect_issues(text: str, url: str | None = None) -> list[str]:
    warnings = []
    words = len(text.split())
    if words < MIN_WORDS:
        warnings.append(f"Content is short ({words} words < {MIN_WORDS} minimum). Proceed with caution.")
    # Simple non-English heuristic: check for common English stopwords
    common_en = {"the", "and", "is", "in", "of", "to", "a", "for", "with", "this"}
    word_set = set(text.lower().split())
    if len(common_en & word_set) < 3:
        warnings.append("Content may not be in English — translation is not supported.")
    return warnings


async def ingest(url: str | None = None, pasted_text: str | None = None) -> IngestionResult:
    if url:
        try:
            raw = await fetch_url(url)
            source_type = "url"
        except RuntimeError as exc:
            # Surface the error so the caller can prompt user to paste
            raise RuntimeError(str(exc)) from exc
    elif pasted_text:
        raw = pasted_text
        source_type = "paste"
    else:
        raise ValueError("Provide either url or pasted_text")

    normalized = normalize(raw)
    warnings = detect_issues(normalized, url)
    return IngestionResult(raw=raw, normalized=normalized, source_type=source_type, warnings=warnings)
