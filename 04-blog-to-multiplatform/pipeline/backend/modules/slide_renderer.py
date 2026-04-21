"""
Playwright slide renderer hook — STUB for future implementation.
Interface defined here; no implementation in v1.

When this is implemented, it will:
1. Take Instagram carousel slide copy (output from the Instagram specialist agent)
2. Render each slide into an HTML template
3. Use Playwright to screenshot each slide as PNG
4. Return a list of image file paths

Usage (future):
    from modules.slide_renderer import render_slides
    images = await render_slides(run_id, slides, template_name="ig_default")
"""
from typing import NotImplemented


async def render_slides(run_id: str, slides: list[dict], template_name: str = "ig_default") -> list[str]:
    """
    Render Instagram carousel slides to PNG images.
    STUB — not implemented in v1.
    Returns empty list. Will return list of image paths in v2.
    """
    return []


def is_available() -> bool:
    """Returns True when Playwright is installed and render_slides is implemented."""
    return False
