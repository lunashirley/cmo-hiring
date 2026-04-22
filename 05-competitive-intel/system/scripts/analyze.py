import os
import re

import anthropic

MODEL = os.environ.get("CLAUDE_MODEL", "claude-haiku-4-5-20251001")
MAX_TOKENS = 8192


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


def _strip_code_fences(text: str) -> str:
    """Remove markdown code fences Claude sometimes wraps around XML output."""
    text = text.strip()
    if text.startswith("```"):
        # Drop the opening fence line (e.g. ```xml)
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
    if text.endswith("```"):
        text = text.rsplit("```", 1)[0]
    return text.strip()


def _extract_tag(text: str, tag: str) -> str:
    text = _strip_code_fences(text)
    match = re.search(rf"<{tag}>(.*?)</{tag}>", text, re.DOTALL)
    if not match:
        raise ValueError(
            f"Could not find <{tag}> block in Claude response.\nRaw response:\n{text[:800]}"
        )
    return match.group(1).strip()


def analyze(
    company_a: str,
    scraped: dict,
    previous_battlecard: str,
    competitor_name: str,
    today: str,
    run_reason: str,
) -> dict:
    """
    Single Claude call: competitor data → battlecard_md + changelog_entry.
    HTML rendering is handled separately by render.py using the markdown library.
    """
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
- Return exactly two XML blocks: <battlecard_md> and <changelog_entry>
- No text outside these two blocks
- Be concise: narrative sections 3–5 sentences max, Objection Handling table 5 rows max
- Total output must stay under 6000 tokens"""

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

Produce the battlecard in this exact Markdown schema:

# Competitive Battlecard: Smartsupp vs. {competitor_name}
**Last Updated:** {today} | **Run Type:** {run_reason}

## TL;DR (For the Rep in a Hurry)
- [bullet 1]
- [bullet 2]
- [bullet 3]

## Pricing Comparison
| Dimension | Smartsupp | {competitor_name} |
|-----------|-----------|---------|
| Entry point | ... | ... |
| Mid-market | ... | ... |
| Enterprise | ... | ... |
| Free tier | ... | ... |

**ICP Perception:** [how the ICP will interpret this comparison]

## Product & Features
[Narrative ICP-focused comparison — not a feature checklist]

**ICP Perception:** [...]

## Messaging & Positioning
[How {competitor_name} describes itself vs. our messaging]

**ICP Perception:** [...]

## Customer Proof (G2)
[Rating, number of reviews, top praise themes, top complaint themes, vs. Smartsupp 4.7/5 from 1,039 reviews]

**ICP Perception:** [...]

## Recent Strategic Signals
[What {competitor_name} is investing in or pivoting toward based on blog and customer content]

## Strategic Implications

### Where We Win
[Specific situations where Smartsupp has a clear advantage with this ICP]

### Where We're Vulnerable
[Honest assessment of where {competitor_name} has the edge]

### Recommended Moves
[Proactive tactics only — positioning moves, discovery questions, demo emphasis. Do not include objection handling or rebuttals here; those belong exclusively in the Objection Handling section below.]

## Objection Handling
| Objection | Recommended Response |
|-----------|----------------------|
| ... | ... |

---

Produce the changelog entry in this exact schema:

## {today} | {run_reason}

### What Changed
- [Material ICP-relevant changes only. If previous_battlecard is NONE: "First run — no prior baseline."]

### Stable (No Material Change)
- [What was checked and unchanged]

### ICP Implication
[One paragraph on what this means for how we sell against {competitor_name}]

---

<battlecard_md>
[full battlecard markdown here]
</battlecard_md>

<changelog_entry>
[changelog entry markdown here]
</changelog_entry>"""

    print(f"  Analyzing with Claude ({MODEL})...")
    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
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
        print("  Warning: response hit max_tokens — output may be truncated")

    raw = response.content[0].text.strip()
    return {
        "battlecard_md": _extract_tag(raw, "battlecard_md"),
        "changelog_entry": _extract_tag(raw, "changelog_entry"),
    }
