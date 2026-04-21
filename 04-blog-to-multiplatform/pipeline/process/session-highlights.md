# Session Highlights — Blog-to-Multiplatform Pipeline (Challenge 04)

**Date:** 21 April 2026
**Repo:** `lunashirley/cmo-hiring` → `04-blog-to-multiplatform/`

---

## What we built

A full-stack multi-agent content repurposing pipeline. Paste or drop a blog URL → AI extracts reusable content atoms → you review and approve them → four specialist agents generate platform-native content → a Head of Content agent QA-reviews every output and retries failures up to 3 times.

**Stack:** FastAPI + SQLite (backend), React 18 + Vite + TypeScript (frontend), Anthropic Claude API or Ollama (LLM).

**Four output channels:** LinkedIn post, X (Twitter) thread, Newsletter section, 60-second video script.

---

## Key decisions made together

| Decision | Why |
|---|---|
| Sequential platform generation (not parallel) | Parallel asyncio.gather silently swallowed X and Newsletter failures; sequential for loop eliminated the issue entirely |
| Rename "x" → "x_twitter" | Single-letter platform names confused the LLM in prompts |
| Replace Instagram with Video Script | Better fit for repurposing written content; clearer structural constraints |
| Named output folders (`busy-season-preparation-guide/`) | More legible than ULIDs for human reviewers |

---

## Bugs we squashed

**Delete outputs (Internal Server Error)** — two separate root causes:
1. `QAResult` FK violation: had to delete child rows before parent `Output` rows
2. `.scalars()` returns raw strings, not ORM objects — `[r.id for r in scalars]` called `.id` on a string

**Atom extraction crash (`could not convert string to float: 'high'`)** — models like deepseek return qualitative confidence labels; added a `_parse_confidence()` normalizer.

**Ghost processes holding port 8000** — couldn't be killed; workaround was moving to port 8003 and updating the Vite proxy.

---

## Agent prompts written/refined

- **LinkedIn "The Authority"** — Hook ≤140 chars, 1,200–2,000 chars, heavy whitespace, open-ended CTA, max 3 hashtags at the end
- **X "The Curator"** — 5–10 tweet thread, 1/N numbering, Hook+Promise opener, standalone RT-able final tweet
- **Newsletter "The Insider"** — 300–600 words, 1-to-1 voice, curiosity subject line, single CTA in bottom third
- **Video Script** — Four-section structure: Pattern Interrupt hook (0–3s) → Value Gap (3–15s) → Numbered Payoff (15–50s) → Loop CTA (50–60s); 130–150 spoken words; alternating `[Visual Action]` and `"Dialogue"` format

---

## Collaboration style that worked

- You caught when I entered consideration loops and redirected decisively ("just rename it and make it sequential")
- Short, direct corrections beat long explanations — the fastest fixes came from you naming the specific change, not the problem
- You tested each fix immediately and reported the exact error or behavior — no ambiguity in feedback

---

## Deliverables on GitHub

```
04-blog-to-multiplatform/
├── pipeline/        ← full app (backend + frontend + agents + templates)
└── output/
    ├── busy-season-preparation-guide/
    └── healthcare-booking-system-2026/
```
