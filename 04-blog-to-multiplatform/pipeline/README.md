# Blog-to-Multiplatform Content Repurposing Pipeline

A multi-agent AI pipeline that ingests a blog post URL (or pasted text) and produces platform-native content for **LinkedIn**, **X (Twitter)**, **Newsletter**, and **Video Script** — with human-in-the-loop review, QA, and a full observability layer.

---

## What it does

1. **Ingests** a blog URL via Jina Reader (or accepts pasted text directly)
2. **Extracts content atoms** — discrete reusable facts, stats, quotes, and insights — using an AI extraction agent
3. **Human review (HITL)** — you approve, edit, reorder, or add atoms before generation
4. **Generates** platform-specific content for all four channels using specialist agents, each with its own structural rules and tone constraints
5. **QA loop** — a Head of Content agent reviews every output against a per-platform rubric; failing outputs are rewritten up to 3 times before being escalated for human review
6. **Stores and exports** all outputs to the `output/` folder as markdown files with full metadata

---

## Architecture

```
pipeline/
├── agents/                  # Agent prompt configs (markdown + frontmatter)
│   ├── atom_extractor.md    # Extracts atoms from article text
│   ├── linkedin.md          # LinkedIn post writer ("The Authority")
│   ├── x_twitter.md         # X/Twitter thread writer ("The Curator")
│   ├── newsletter.md        # Newsletter section writer ("The Insider")
│   ├── video_script.md      # 60s video scriptwriter
│   └── head_of_content.md   # QA reviewer with per-platform rubric
├── templates/               # Structural constraints per platform
│   ├── linkedin.md
│   ├── x_twitter.md
│   ├── newsletter.md
│   └── video_script.md
├── brand_voices/            # Brand voice profiles (markdown)
│   └── default.md           # Reservio brand voice
├── backend/                 # FastAPI (Python 3.11+)
│   ├── main.py              # API routes and background task orchestration
│   ├── database.py          # SQLite async engine (WAL mode)
│   ├── models.py            # SQLAlchemy ORM models
│   ├── llm.py               # LLM client: Ollama + Anthropic Claude API
│   ├── agent_loader.py      # Hot-reloading agent/template/brand-voice loader
│   ├── auth.py              # Single-user session auth (JWT cookie)
│   ├── config.py            # Settings defaults and path constants
│   └── modules/
│       ├── ingestion.py     # Jina Reader + paste fallback
│       ├── extraction.py    # Atom extraction agent runner
│       ├── orchestration.py # Specialist agents + HoC QA loop
│       └── learning.py      # Logging, ratings, exemplar pool, versioning
└── frontend/                # React 18 + Vite + TypeScript
    └── src/
        ├── tabs/
        │   ├── Pipeline.tsx     # Main pipeline flow (input → HITL → generation)
        │   ├── Outputs.tsx      # View, edit, export, delete generated outputs
        │   ├── Ratings.tsx      # Rate outputs 1–5 with tags
        │   ├── BrandVoices.tsx  # Edit brand voice profiles in-app
        │   ├── Agents.tsx       # Edit agent prompts and view version history
        │   ├── Logs.tsx         # Per-run and per-agent event logs
        │   └── Settings.tsx     # Model, provider, concurrency config
        └── components/
            ├── AtomCard.tsx         # Drag-and-drop atom editor
            └── GenerationStream.tsx # Real-time SSE progress display
```

---

## Multi-agent pipeline

### Agents

| Agent | Role | Key behaviour |
|---|---|---|
| `atom_extractor` | Reads the article, returns 8–15 typed atoms (stat, insight, quote, anecdote) | Retries once on malformed JSON; confidence normalised from string labels |
| `linkedin` | "The Authority" — structured LinkedIn post | Hook ≤140 chars, 1,200–2,000 chars, heavy whitespace, open-ended CTA |
| `x_twitter` | "The Curator" — tweet thread | 5–10 tweets, Hook+Promise tweet 1, numbered 1/N, Next Step final tweet |
| `newsletter` | "The Insider" — editorial section | 300–600 words, bold subheadings, 1-to-1 voice, single CTA |
| `video_script` | 60-second short-form video script | Pattern Interrupt hook, numbered payoff, Loop CTA, 130–150 spoken words |
| `head_of_content` | QA reviewer | Per-platform rubric; returns pass/fail + structured rework notes |

### QA loop

Each platform runs through the following cycle:

```
Specialist agent → Head of Content review
  → pass: output saved as "approved"
  → fail: rework notes injected into next attempt → retry (max 3)
         → 3rd failure: output saved as "escalated" for human review
```

### Exemplar learning

Outputs you rate 4–5 stars are automatically injected as few-shot examples into the next generation for that platform and brand voice, improving consistency over time without any code changes.

---

## Supported LLM providers

| Provider | How to configure |
|---|---|
| **Anthropic Claude API** | Set provider to `anthropic` in Settings, paste your API key |
| **Ollama (local)** | Set provider to `ollama`, set endpoint (default `http://localhost:11434`), set model name |

Recommended models: `claude-sonnet-4-5` (Anthropic) or `deepseek-r1:8b` (Ollama).

---

## Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- An Anthropic API key **or** Ollama running locally with a model pulled

### 1. Backend

```bash
cd pipeline/backend

# Create and activate virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt

uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The backend starts at `http://localhost:8000`. SQLite (`pipeline.db`) is created automatically at the project root on first start.

**Default login:** username `admin`, password `admin`
Override the password via the `PIPELINE_PASSWORD` environment variable.

### 2. Frontend

```bash
cd pipeline/frontend
npm install
npm run dev
```

Opens at `http://localhost:5173`. The Vite dev server proxies `/api` calls to the backend at port 8000.

### 3. Configure provider and model

Open the app → **Settings** tab:

- **Provider:** choose `Anthropic` and paste your API key, or `Ollama` and set the endpoint + model name
- **QA Max Attempts:** how many times the HoC can reject and rewrite an output (default 3)
- **Max Concurrency:** parallel platform slots — set to 1 if hitting rate limits (default 2)

---

## Running a pipeline run

1. **Pipeline tab** → paste a blog URL or raw article text → click **Start Pipeline**
2. Wait for extraction (15–60s depending on article length and model speed)
3. **Review atoms** in the HITL screen:
   - Toggle approval checkboxes
   - Edit atom text inline
   - Reorder by drag-and-drop
   - Delete irrelevant atoms
   - Add manual atoms not caught by the extractor
4. **Select brand voice** from the dropdown
5. Click **Generate Content** — the real-time progress panel shows each platform's status live
6. Switch to the **Outputs tab** to view, edit, rate, and export the results

Generated content is also auto-exported to `output/run_<id>/` as individual markdown files.

---

## Editing agents and brand voices

All agent prompts, QA rubrics, and brand voice profiles are plain markdown files. You can edit them:

- **Directly** in `pipeline/agents/` and `pipeline/brand_voices/` — changes take effect on the next run with no server restart
- **In-app** via the Agents and Brand Voices tabs — edits are saved to disk and each previous version is snapshotted automatically for diff and rollback

The template files in `pipeline/templates/` define the structural constraints (character limits, format rules) that are injected into the specialist agent prompts.

---

## Output folder structure

Each run produces a folder under `output/`:

```
output/
└── run_<ulid>/
    ├── source.md        # Original article text
    ├── atoms.json       # Extracted and approved atoms with metadata
    ├── linkedin.md      # LinkedIn post
    ├── x_twitter.md     # X (Twitter) thread
    ├── newsletter.md    # Newsletter section
    └── video_script.md  # 60-second video script
```

---

## Observability

### Logs tab
Every LLM call is logged with: agent, event type (start / response / retry / pass / fail / error), attempt number, duration (ms), and token counts. Filter by run, agent, or event type.

### Scorecards
The Logs tab shows per-agent scorecards: total calls, average response time, retry rate, and pass rate — useful for spotting which agents or models are underperforming.

### Ratings
Rate any output 1–5 stars with optional tags (hook, length, CTA, tone, format, etc.) and a free-text note. High-rated outputs feed back into future generations as exemplars.

---

## Key design decisions

| Decision | Reason |
|---|---|
| SQLite with WAL mode | No database server required; concurrent reads safe during writes |
| Server-Sent Events for progress | Real-time platform-by-platform status without polling |
| Sequential platform generation | Avoids concurrent write contention and LLM rate limits |
| Agent configs as markdown | Prompt changes require no code deploys; hot-reloaded on every run |
| Brand voice injection | Every specialist receives the full brand profile; HoC checks conformance |
| ULID-based IDs | Sortable by creation time; no UUID collision risk |
