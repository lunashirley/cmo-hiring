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
    # Use DOTALL so . matches newlines
    match = re.search(rf"<{tag}>(.*?)</{tag}>", text, re.DOTALL)
    if not match:
        raise ValueError(f"Could not find <{tag}> block in Claude response")
    return match.group(1).strip()


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

    system_prompt = f"""You are a competitive intelligence analyst producing battlecards for sales and marketing teams.

Always reason from the perspective of the Ideal Customer Profile (ICP):
{icp_definition}

Company A (our company):
<company_a>
{company_a}
</company_a>

Output rules:
- Wrap each section in XML tags exactly as shown — no text outside the tags
- <battlecard_md>: full battlecard in Markdown
- <battlecard_html>: complete standalone HTML with inline CSS — clean professional design, readable typography, suitable for PDF rendering, no external dependencies or CDN links
- <changelog_entry>: a single Markdown changelog entry for this run"""

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
- [Only material ICP-relevant changes since the previous battlecard: pricing shifts, new features announced, messaging pivots, G2 rating moves. If previous_battlecard is NONE, write "First run — no prior baseline."]

### Stable (No Material Change)
- [What was checked and unchanged]

### ICP Implication
[One paragraph: what these changes mean for how we position and sell against {competitor_name}]

---

Return your response using exactly these three XML tags:

<battlecard_md>
[markdown battlecard here]
</battlecard_md>

<battlecard_html>
[complete standalone HTML document here]
</battlecard_html>

<changelog_entry>
[markdown changelog entry here]
</changelog_entry>"""

    print(f"  Calling Claude ({MODEL})...")
    response = client.messages.create(
        model=MODEL,
        max_tokens=8192,
        system=[
            {
                "type": "text",
                "text": system_prompt,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw = response.content[0].text.strip()

    if response.stop_reason == "max_tokens":
        print("  Warning: response hit max_tokens limit — output may be truncated")

    return {
        "battlecard_md": _extract_tag(raw, "battlecard_md"),
        "battlecard_html": _extract_tag(raw, "battlecard_html"),
        "changelog_entry": _extract_tag(raw, "changelog_entry"),
    }
