import os
import re

import anthropic

MODEL = os.environ.get("CLAUDE_MODEL", "claude-haiku-4-5-20251001")


def _extract_icp_definition(company_a: str) -> str:
    lines = company_a.split("\n")
    in_icp = False
    icp_lines: list[str] = []
    for line in lines:
        if line.strip().startswith("## ICP Definition"):
            in_icp = True
            continue
        if in_icp:
            if line.startswith("## "):
                break
            icp_lines.append(line)
    return "\n".join(icp_lines).strip()


def _extract_tag(text: str, tag: str) -> str:
    match = re.search(rf"<{tag}>(.*?)</{tag}>", text, re.DOTALL)
    if not match:
        raise ValueError(f"Could not find <{tag}> block in Claude response")
    return match.group(1).strip()


def _call_1_analysis(
    client: anthropic.Anthropic,
    company_a: str,
    icp_definition: str,
    scraped_sections: str,
    previous_battlecard: str,
    competitor_name: str,
    today: str,
    run_reason: str,
) -> tuple[str, str]:
    """Generate battlecard markdown + changelog entry."""

    system_prompt = f"""You are a competitive intelligence analyst producing battlecards for sales and marketing teams.

Always reason from the perspective of the Ideal Customer Profile (ICP):
{icp_definition}

Company A (our company):
<company_a>
{company_a}
</company_a>

Output rules:
- Return exactly two XML blocks: <battlecard_md> and <changelog_entry>
- No text outside these tags"""

    user_prompt = f"""Competitor: {competitor_name}
Run date: {today}
Run type: {run_reason}

<competitor_data>
{scraped_sections}
</competitor_data>

<previous_battlecard>
{previous_battlecard}
</previous_battlecard>

---

Produce the battlecard using this exact Markdown schema:

# Competitive Battlecard: Company A vs. {competitor_name}
**Last Updated:** {today} | **Run Type:** {run_reason}

## TL;DR (For the Rep in a Hurry)
[3 bullets max — the most important things a rep needs to know right now]

## Pricing Comparison
[Table comparing key pricing dimensions]
**ICP Perception:** [how the ICP will interpret this comparison]

## Product & Features
[Narrative ICP-focused comparison — not a feature checklist]
**ICP Perception:** [...]

## Messaging & Positioning
[How {competitor_name} describes itself vs. our messaging and claimed jobs-to-be-done]
**ICP Perception:** [...]

## Customer Proof (G2)
[Rating, number of reviews, top praise themes, top complaint themes, comparison to our G2 presence]
**ICP Perception:** [...]

## Recent Strategic Signals
[What {competitor_name} is investing in, announcing, or pivoting toward based on blog content]

## Strategic Implications
### Where We Win
### Where We're Vulnerable
### Recommended Moves

## Objection Handling
| Objection | Recommended Response |
|-----------|----------------------|

---

Produce the changelog entry using this exact schema:

## {today} | {run_reason}

### What Changed
- [Only material ICP-relevant changes since the previous battlecard. If previous_battlecard is NONE, write "First run — no prior baseline."]

### Stable (No Material Change)
- [What was checked and unchanged]

### ICP Implication
[One paragraph: what these changes mean for how we position and sell against {competitor_name}]

---

<battlecard_md>
[markdown battlecard here]
</battlecard_md>

<changelog_entry>
[markdown changelog entry here]
</changelog_entry>"""

    print(f"  Call 1/2 — analysis ({MODEL})...")
    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=[
            {
                "type": "text",
                "text": system_prompt,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": user_prompt}],
    )

    if response.stop_reason == "max_tokens":
        print("  Warning: Call 1 hit max_tokens — output may be truncated")

    raw = response.content[0].text.strip()
    return _extract_tag(raw, "battlecard_md"), _extract_tag(raw, "changelog_entry")


def _call_2_html(
    client: anthropic.Anthropic,
    battlecard_md: str,
    competitor_name: str,
    today: str,
) -> str:
    """Convert finished battlecard markdown into a styled standalone HTML document."""

    system_prompt = """You are a professional document designer. Convert the provided competitive battlecard Markdown into a polished, standalone HTML document.

Design rules:
- Inline CSS only — no external stylesheets, no CDN links, no web fonts
- Clean sans-serif font stack (system-ui, -apple-system, Segoe UI, Arial)
- Light background (#f8f9fa), white content card, subtle shadows
- Section headings in deep navy (#1a2744), body text in dark grey (#333)
- Tables: alternating row shading, header in navy with white text
- TL;DR section: highlighted box (light blue background) to draw the eye
- Strategic Implications: colour-coded — green tint for "Where We Win", amber tint for "Where We're Vulnerable"
- Page-ready layout: max-width 900px, generous padding, suitable for WeasyPrint PDF rendering
- Output: a single complete <html>...</html> document wrapped in <battlecard_html> tags"""

    user_prompt = f"""Convert this battlecard to HTML:

<battlecard_md>
{battlecard_md}
</battlecard_md>

Competitor: {competitor_name} | Date: {today}

<battlecard_html>
[complete standalone HTML document here]
</battlecard_html>"""

    print(f"  Call 2/2 — HTML render ({MODEL})...")
    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )

    if response.stop_reason == "max_tokens":
        print("  Warning: Call 2 hit max_tokens — HTML may be truncated")

    raw = response.content[0].text.strip()
    return _extract_tag(raw, "battlecard_html")


def analyze(
    company_a: str,
    scraped: dict,
    previous_battlecard: str,
    competitor_name: str,
    today: str,
    run_reason: str,
) -> dict:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    icp_definition = _extract_icp_definition(company_a)

    scraped_sections = "\n\n".join(
        f"<{key}>\nSource: {data['url']}\n\n{data['content']}\n</{key}>"
        for key, data in scraped.items()
    )

    battlecard_md, changelog_entry = _call_1_analysis(
        client=client,
        company_a=company_a,
        icp_definition=icp_definition,
        scraped_sections=scraped_sections,
        previous_battlecard=previous_battlecard,
        competitor_name=competitor_name,
        today=today,
        run_reason=run_reason,
    )

    battlecard_html = _call_2_html(
        client=client,
        battlecard_md=battlecard_md,
        competitor_name=competitor_name,
        today=today,
    )

    return {
        "battlecard_md": battlecard_md,
        "battlecard_html": battlecard_html,
        "changelog_entry": changelog_entry,
    }
