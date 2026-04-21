"""
Hot-reloading loader for agent .md and template .md config files.
Reads frontmatter version and full content on each call — no caching,
so file changes take effect on the next run automatically.
"""
import re
from pathlib import Path
from config import AGENTS_DIR, TEMPLATES_DIR, BRAND_VOICES_DIR


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """Return (frontmatter_dict, body_text). Frontmatter is YAML-ish key: value pairs."""
    fm: dict = {}
    body = text
    if text.startswith("---"):
        end = text.find("---", 3)
        if end != -1:
            header = text[3:end].strip()
            body = text[end + 3:].strip()
            for line in header.splitlines():
                if ":" in line:
                    k, _, v = line.partition(":")
                    raw = v.strip().strip('"')
                    if raw.isdigit():
                        fm[k.strip()] = int(raw)
                    elif raw.lower() in ("null", ""):
                        fm[k.strip()] = None
                    elif raw.lower() == "true":
                        fm[k.strip()] = True
                    elif raw.lower() == "false":
                        fm[k.strip()] = False
                    else:
                        fm[k.strip()] = raw
    return fm, body


def load_agent(name: str) -> dict:
    path = AGENTS_DIR / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(f"Agent config not found: {path}")
    text = path.read_text(encoding="utf-8")
    fm, body = _parse_frontmatter(text)
    return {"name": name, "version": fm.get("version", 1), "content": text, "body": body, "path": str(path)}


def load_template(platform: str) -> dict:
    path = TEMPLATES_DIR / f"{platform}.md"
    if not path.exists():
        raise FileNotFoundError(f"Template not found: {path}")
    text = path.read_text(encoding="utf-8")
    fm, body = _parse_frontmatter(text)
    return {"platform": platform, "version": fm.get("version", 1), "content": text, "body": body}


def load_brand_voice(slug: str) -> dict | None:
    path = BRAND_VOICES_DIR / f"{slug}.md"
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")
    fm, body = _parse_frontmatter(text)
    return {"slug": slug, "name": fm.get("name", slug), "version": fm.get("version", 1), "content": text, "body": body}


def list_brand_voices() -> list[dict]:
    voices = []
    for path in sorted(BRAND_VOICES_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        fm, _ = _parse_frontmatter(text)
        voices.append({
            "slug": path.stem,
            "name": fm.get("name", path.stem),
            "version": fm.get("version", 1),
            "archived": fm.get("archived", False),
        })
    return voices


def list_agents() -> list[dict]:
    agents = []
    for path in sorted(AGENTS_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        fm, _ = _parse_frontmatter(text)
        agents.append({
            "name": path.stem,
            "version": fm.get("version", 1),
        })
    return agents


def save_agent(name: str, content: str) -> None:
    path = AGENTS_DIR / f"{name}.md"
    path.write_text(content, encoding="utf-8")


def save_brand_voice(slug: str, content: str) -> None:
    path = BRAND_VOICES_DIR / f"{slug}.md"
    path.write_text(content, encoding="utf-8")


def extract_prompt_section(body: str) -> str:
    """Extract the ## Prompt section from agent body."""
    match = re.search(r"## Prompt\s*\n(.*)", body, re.DOTALL)
    if match:
        return match.group(1).strip()
    return body
