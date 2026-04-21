# Content Repurposing Pipeline — PoC Specification

**Owner:** Luna
**Status:** Planning — ready for build
**Deployment:** Local (localhost)
**Purpose:** Atomize a single blog URL into platform-native content for LinkedIn, X (Twitter), Newsletter, and Instagram Carousel, with human validation, multi-agent generation, QA, and a lightweight feedback loop.

---

## 1. Scope

### In scope
- URL ingestion via Jina Reader, with copy/paste fallback.
- Atom extraction with typed schema.
- Human-in-the-Loop (HITL) atom validation with edit, retype, reorder (drag and drop), add, delete.
- Four platform specialist agents: LinkedIn, X, Newsletter, Instagram Carousel (copy only, no image rendering).
- Head of Content (HoC) QA agent with per-platform rubric.
- Retry loop capped at 3 attempts per output before escalation.
- Parallel agent execution (hardware-permitting).
- Post-generation output editing by the operator, with diff capture.
- Impact rating and lightweight structured reason tagging.
- Brand voice profiles (multi), selectable at HITL.
- Per-agent markdown configuration files as source of truth for prompts and rubrics.
- Structured, per-agent action logs viewable in a dedicated UI tab.
- Simple local login (single user, password-based).
- Restartable stages, persistent run state.
- Local inference via Ollama (default `qwen3-vl:30b`, configurable in settings).
- Saved outputs (versioned, exportable).

### Out of scope (this iteration)
- Direct publishing or scheduling to any platform.
- Image generation (including IG slide rendering). Structure will be prepared for Playwright + HTML templates in a later iteration; no implementation now.
- Multi-language output.
- Per-agent model overrides (single model used across agents in v1; design leaves room for later).
- Multi-user accounts, OAuth, SSO.

---

## 2. High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                              FastAPI Backend                             │
│                                                                          │
│  ┌────────────────────┐    ┌───────────────────────────────────────────┐ │
│  │  Module A           │    │  Module B                                 │ │
│  │  Ingestion &        │───▶│  Agent Orchestration & Brand Voice        │ │
│  │  Atom Extraction    │    │  (Specialists + HoC QA, parallel, retries)│ │
│  └────────────────────┘    └───────────────────────────────────────────┘ │
│           │                              │                               │
│           ▼                              ▼                               │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  Module C                                                         │    │
│  │  Learning & Observability                                         │    │
│  │  (Rating, Feedback Loop, Templating, Versioning, Logging)         │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  SQLite (runs, atoms, outputs, edits, ratings, logs, brand_voices)      │
└──────────────────────────────────────────────────────────────────────────┘
                                   ▲
                                   │
                              REST / SSE
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                           React Frontend                                 │
│                                                                          │
│   Tabs: Pipeline | Outputs | Ratings | Brand Voices | Logs | Settings   │
└──────────────────────────────────────────────────────────────────────────┘
```

### The three modules

**Module A — Ingestion & Atom Extraction**
Fetch, normalize, extract structured atoms. Treated as one cohesive module because atom extraction is only meaningful against ingested text, and the schema boundary between them is trivial.

**Module B — Agent Orchestration & Brand Voice**
Runs specialists and HoC in a managed workflow. Brand voice lives here because voice is applied at agent-run time and has no independent lifecycle from orchestration.

**Module C — Learning & Observability**
Ratings, feedback injection, template and prompt versioning, structured logs. One module because every item here writes to or reads from the same append-only event stream.

---

## 3. Tech Stack

| Layer | Choice | Rationale |
|---|---|---|
| Backend | FastAPI (Python 3.11+) | Async-native, clean dependency injection, Pydantic schemas align with atom typing. |
| Frontend | React + Vite + TypeScript | Matches Cortex familiarity; typed contracts with backend. |
| UI components | Tailwind + shadcn/ui | Fast composition, clean defaults. |
| Drag and drop | dnd-kit | Modern, accessible, smooth transitions. |
| State | TanStack Query (server), Zustand (client) | Clear split between server cache and local UI state. |
| DB | SQLite via SQLAlchemy (async) | Zero-config local persistence; easy migration later. |
| Inference | Ollama HTTP API | Local, simple, model-swappable via settings. |
| Parallelism | `asyncio.gather` with bounded semaphore | Respects hardware; configurable concurrency cap. |
| Real-time UI | Server-Sent Events (SSE) | Streams agent progress and logs without WS complexity. |
| Auth | Single-user password + signed session cookie | Localhost only; no OAuth, no registration. |
| Logs | Structured JSON to SQLite + stdout mirror | Queryable in UI, tailable in terminal. |

---

## 4. Module A — Ingestion & Atom Extraction

### 4.1 Ingestion

**Inputs**
- `url` (string) — preferred path, fetched via Jina Reader: `https://r.jina.ai/{url}`.
- `pasted_text` (string) — fallback for paywalled, gated, or private content.

**Behavior**
- If `url` is provided, call Jina Reader with a 20s timeout and 2 retries (exponential backoff).
- On failure, surface a clear UI prompt to paste content manually; do not silently fall through.
- Normalize to clean text: strip boilerplate, deduplicate whitespace, preserve paragraph breaks.
- Persist raw and normalized content against `run_id`.

**Failure modes handled**
- Jina returns empty or HTML-error page — flagged and user prompted.
- Content under 300 words — warning surfaced; user may proceed or abort.
- Non-English detection (simple heuristic) — warning, proceed allowed (out-of-scope for translation, but visibility preserved).

### 4.2 Atom Extraction

**Atom schema**

```json
{
  "id": "atom_<ulid>",
  "type": "stat | insight | quote | anecdote",
  "text": "string",
  "source_offset": { "start": 0, "end": 0 },
  "proposed_angle": "string, one-line on why this matters",
  "confidence": 0.0,
  "origin": "extracted | manual",
  "priority": 0
}
```

**Agent**
- `atom_extractor.md` defines the extractor prompt and output contract (see Section 9).
- Outputs strict JSON validated against the schema; malformed responses trigger a single retry with a "return valid JSON only" nudge, then fail visibly.
- Targets 8–15 atoms per article; configurable in settings.

**Typing conventions**
- `stat`: any quantified claim, figure, or measurable outcome.
- `insight`: non-obvious interpretation or framing.
- `quote`: verbatim lift worth preserving.
- `anecdote`: short narrative or example.

### 4.3 HITL Checkpoint — UX

The HITL screen is the most important human interaction in the pipeline. It should feel composed, never busy.

**Capabilities**
- Reorder atoms via drag and drop (dnd-kit), with soft transitions (motion reduced if user prefers).
- Inline edit text without leaving the list.
- Retype (change atom type via dropdown).
- Delete with undo toast (5s window).
- Add manual atom (`origin = manual`).
- Select brand voice profile from dropdown (required before proceeding).
- "Proceed to generation" is disabled until at least one atom is approved and a brand voice is selected.

**Visual state**
- Atoms show a colored type tag and a confidence indicator (extracted atoms only).
- Edited atoms display a subtle "edited" marker; original text is recoverable via hover.

---

## 5. Module B — Agent Orchestration & Brand Voice

### 5.1 Agent roster

| Agent | Role | Config file |
|---|---|---|
| Atom Extractor | Extracts typed atoms from source text | `agents/atom_extractor.md` |
| LinkedIn Specialist | Platform-native post | `agents/linkedin.md` |
| X Specialist | Single post or short thread | `agents/x.md` |
| Newsletter Specialist | Short-form newsletter section | `agents/newsletter.md` |
| Instagram Specialist | Carousel slide copy (8–10 slides) | `agents/instagram.md` |
| Head of Content (HoC) | QA against per-platform rubric | `agents/head_of_content.md` |

All agent files live in `/agents` and are hot-reloaded on change (no server restart needed).

### 5.2 Orchestration flow

```
Atoms approved + brand voice selected
        │
        ▼
  Parallel fan-out (bounded semaphore, configurable max_concurrency)
  ─────────────┬────────────┬───────────────┬────────────
  │ LinkedIn  │     X     │  Newsletter  │ Instagram  │
  ───────┬─────┴──────┬─────┴───────┬──────┴──────┬──────
        │           │            │             │
        ▼           ▼            ▼             ▼
   HoC review (parallel per output)
        │
        ▼
   Pass? → store as "approved"
   Fail? → attempt < 3 → return to specialist with HoC notes injected
            attempt = 3 → store as "escalated" with full QA trace, surfaced in UI
```

**Parallelism safeguards**
- `max_concurrency` setting (default 2) caps simultaneous model calls.
- If any single call exceeds `per_call_timeout` (default 120s), it is terminated and retried once.
- If combined run exceeds `run_timeout` (default 10 min), operator is prompted to continue or abort.

**Rework prompt**
When an output is returned for rework, the specialist receives:
- Original atoms (unchanged)
- Brand voice (unchanged)
- Previous output
- HoC's structured feedback (rubric-item-keyed)
- Explicit instruction to address each failed rubric item

### 5.3 Brand Voice

**Brand voice markdown file schema** (`brand_voices/<slug>.md`):

```markdown
---
name: "Pattern GTM"
slug: "pattern-gtm"
created: "2026-04-20"
version: 3
---

## Tone descriptors
Direct, commercial, warm-but-efficient, zero corporate filler.

## Vocabulary — do
- "commercial", "deliberate", "dependency", "playbook"

## Vocabulary — don't
- "synergy", "leverage" (as verb), "unlock", em dashes

## Sentence preferences
- Short-to-medium length. Avoid three clauses in one sentence.

## CTA patterns
- End with a direct question or a single clear action.

## Reference examples
- (paste 2–3 exemplar pieces)
```

- Stored as files for easy version control, diffing, and portability.
- Loaded into a `brand_voice` registry at startup and on file change.
- Operator can create, edit, duplicate, and archive profiles from the Brand Voices tab.
- The selected profile's full markdown is injected into every content-producing agent's prompt.

### 5.4 Agent execution contract

Each agent call:
1. Loads its `.md` config (prompt, output format, constraints).
2. Receives: atoms, brand voice, platform template, and (where relevant) top-3 exemplars from feedback loop (Section 6.3).
3. Returns a JSON envelope:
   ```json
   {
     "output": "string or structured payload",
     "metadata": { "atom_ids_used": [...], "notes": "optional" }
   }
   ```
4. Logs inputs, outputs, duration, and token counts to the per-agent log stream.

---

## 6. Module C — Learning & Observability

### 6.1 Output storage and editing

**Storage**
- Each generated output is stored as a versioned row: `(run_id, platform, version, content, status)`.
- `status ∈ {draft, approved, escalated, edited, final}`.
- When the operator edits an output, the edit is stored as a **diff** (unified diff format) against the previous version, not a full copy. Keeps storage lean and makes learning signal explicit.
- Final versions are exportable as `.md`, `.txt`, or `.json` from the Outputs tab.

### 6.2 Rating system (lightweight, fast)

**Design principle:** the operator should rate in under 10 seconds per output. No mandatory explanation fields.

**Rating UI**
- 5-point impact scale: Worst, Low, Average, High, Best (stored as 1–5).
- A single optional multi-select: "What drove this?"
  - Options: `hook`, `length`, `CTA`, `atom choice`, `tone`, `format`, `timing`, `other`.
  - Zero to three tags allowed. No tag required.
- Optional free-text note (collapsed by default; operator can expand if they want to).

**Rationale**
- The 5-point scale carries impact.
- Multi-select tags carry attribution without forcing an essay.
- Edits (Section 6.1) carry implicit signal about what was wrong, independently of rating.

Together these three signals — rating, tags, edit diff — give the feedback loop enough structure to learn from without burdening the operator.

### 6.3 Feedback loop — few-shot injection

**Mechanism (v1, pragmatic)**
- For each `(platform, brand_voice)` pair, maintain a rolling pool of the top 5 outputs by rating, recency-weighted.
- On each new generation, the top 3 are injected into the specialist's prompt as exemplars, with their tags ("this worked because of: hook, CTA").
- Edited versions take precedence over original generated versions in the exemplar pool — the operator's edit is the ground truth.

**Why this over fine-tuning**
- Local, zero-infrastructure, immediate feedback.
- Transparent: operator can see which exemplars are currently seeding the pool.
- Reversible: exemplars can be manually excluded from the pool if they start distorting output.

### 6.4 Templates and versioning

- Platform templates live in `/templates/<platform>.md` and define structural constraints (character caps, slide counts, heading conventions, link placement).
- Every agent `.md` and template `.md` is versioned in-file (frontmatter `version:` counter).
- On change, previous version is snapshotted into `template_versions` / `agent_versions` tables with timestamp.
- Each run records the exact version IDs used, so any output can be reproduced from its original inputs.

### 6.5 Logging

**Every agent action emits a structured log event:**

```json
{
  "ts": "ISO-8601",
  "run_id": "run_<ulid>",
  "agent": "linkedin | x | newsletter | instagram | hoc | extractor",
  "event": "start | prompt | response | retry | pass | fail | error",
  "attempt": 1,
  "duration_ms": 0,
  "token_in": 0,
  "token_out": 0,
  "payload_ref": "sha256 of prompt/response, stored in blob table",
  "notes": "optional"
}
```

**Logs tab UI**
- Filterable by `run_id`, `agent`, `event`, date range.
- Per-agent view shows: call count, avg duration, retry rate, pass rate, avg rating of downstream output.
- This directly answers the "validate their added value" requirement — HoC and every specialist get a measurable scorecard.

---

## 7. Data Model (SQLite)

```
runs                (id, url, source_type, raw_ref, normalized_ref, status, brand_voice_slug, created_at)
atoms               (id, run_id, type, text, source_offset, proposed_angle, confidence, origin, priority, approved)
outputs             (id, run_id, platform, version, content, status, agent_version, template_version, created_at)
output_edits        (id, output_id, diff, edited_at)
ratings             (id, output_id, score, tags_json, note, rated_at)
qa_results          (id, output_id, attempt, verdict, rubric_json, created_at)
brand_voices        (slug, name, version, content_md, archived)
agent_versions      (agent, version, content_md, created_at)
template_versions   (platform, version, content_md, created_at)
logs                (id, ts, run_id, agent, event, attempt, duration_ms, token_in, token_out, payload_ref, notes)
payload_blobs       (sha256, content)   -- deduped prompt/response storage
settings            (key, value)        -- model, max_concurrency, timeouts, atom target
users               (id, username, password_hash)   -- single row in v1
```

---

## 8. Frontend Tabs

**Pipeline** — the run flow: URL input → extraction progress → HITL atoms → generation progress → outputs.
**Outputs** — browse all runs and their outputs, edit, rate, export.
**Ratings** — aggregate view: per-platform performance, top tags, rating trends.
**Brand Voices** — list, create, edit, duplicate, archive profiles (markdown editor with preview).
**Agents** — view and edit each agent's `.md` config with version history (same editor component as brand voices).
**Logs** — filterable event log with per-agent scorecards.
**Settings** — Ollama endpoint, model name, concurrency cap, timeouts, atom target range, login password change.

---

## 9. Agent `.md` File Convention

Each agent file in `/agents/*.md` follows this structure:

```markdown
---
agent: "linkedin"
version: 4
model_override: null   # reserved, unused in v1
---

## Role
One-paragraph definition of the agent's job.

## Inputs
- atoms (schema reference)
- brand_voice (full md)
- template (platform md)
- exemplars (optional, top-3)
- rework_notes (optional, HoC feedback)

## Output format
Strict JSON envelope (see Section 5.4).

## Constraints
- Hard rules that cannot be violated (e.g., X post ≤ 280 chars).

## Prompt
(Full system + user prompt template with {{placeholders}})

## Rubric (HoC only)
- Checklist of pass/fail criteria with weights, per platform.
```

**HoC rubric example structure** (in `head_of_content.md`):

Per platform, a checklist like:
- `hook_strength` — opens with a pattern interrupt or specific claim, not a generic setup.
- `length_band` — within platform constraints.
- `atom_fidelity` — at least N atoms clearly represented.
- `tone_match` — aligns with brand voice do/don't lists.
- `cta_presence` — has a clear close.
- `banned_phrasings` — no tokens from brand voice's don't list.

HoC returns a structured verdict:
```json
{
  "verdict": "pass | fail",
  "rubric": {
    "hook_strength": { "pass": true, "note": "..." },
    "length_band": { "pass": false, "note": "12 chars over cap" },
    ...
  }
}
```

---

## 10. Settings (default values)

| Setting | Default | Notes |
|---|---|---|
| `ollama_endpoint` | `http://localhost:11434` | Editable |
| `model` | `qwen3-vl:30b` | Editable |
| `max_concurrency` | 2 | Tune to hardware |
| `per_call_timeout_s` | 120 | |
| `run_timeout_s` | 600 | |
| `atom_target_min` | 8 | |
| `atom_target_max` | 15 | |
| `qa_max_attempts` | 3 | |
| `exemplar_pool_size` | 5 | |
| `exemplars_injected` | 3 | |

---

## 11. Build Phases

**Phase 1 — Foundation (Module A + skeleton UI)**
- FastAPI scaffold, SQLite, auth, settings tab.
- Ingestion (Jina + paste).
- Atom extractor + HITL screen with drag and drop, edit, add, delete.

**Phase 2 — Generation (Module B)**
- Brand voice profile loader and UI.
- Four specialist agents + HoC.
- Parallel execution with retry loop.
- Outputs tab (view + edit + export).

**Phase 3 — Learning (Module C)**
- Rating UI with tags.
- Exemplar pool and few-shot injection.
- Versioning for templates and agents.
- Logs tab with per-agent scorecards.

**Phase 4 — Polish**
- Edge case handling (empty Jina results, oversized articles, malformed atom JSON).
- Undo/redo in HITL.
- Export formats.
- Prep hooks for future Playwright slide rendering (interface defined, not implemented).

---

## 12. Non-Goals to Defend Against

These are the drifts most likely to derail a PoC. Spec will resist them:

- Adding publish/schedule features.
- Adding image generation.
- Adding user management.
- Adding multiple model providers (OpenAI, Anthropic hosted) before the local loop is solid.
- Replacing few-shot injection with fine-tuning before there is enough rating data to justify it.
- Making brand voice a form with fields instead of a markdown file. Markdown stays.

---

## 13. Success Criteria for PoC

- One URL → four platform-native outputs in under 5 minutes on target hardware.
- At least 80% of generated outputs pass HoC on first or second attempt.
- Operator can complete a full run (ingest → rate) in under 10 minutes end-to-end.
- Every agent's added value is observable in the Logs tab (retry rate, pass rate, downstream rating).
- Brand voice changes in the `.md` file take effect on next run without restart.
- A run started yesterday can be resumed from any stage today.

---

## 14. Open Items for First Build Session

- Confirm default login credentials handling (env var vs first-run setup).
- Confirm SQLite file location and backup convention.
- Decide on export file naming convention (`{run_id}_{platform}_v{n}.md` proposed).
- Decide whether HITL screen should support bulk-approve (proposed: yes, one-click approve all then edit as needed).
