# 05 — Competitive Intelligence Pipeline

An automated competitive intelligence system that scrapes competitor sources weekly, compares them against your company profile using Claude AI, and commits a designed battlecard PDF + structured changelog directly to this repository.

---

## What It Does

| Step | What happens |
|------|-------------|
| **Trigger** | GitHub Actions fires every Monday 9am UTC, or on demand |
| **Scrape** | Firecrawl fetches competitor URLs (pricing, blog, G2, etc.) and returns clean markdown |
| **Analyze** | Claude reads scraped content + your company profile and produces a battlecard + changelog entry |
| **Render** | Python `markdown` library + CSS template converts the battlecard to HTML; WeasyPrint generates a PDF |
| **Commit** | All outputs committed back to this repo under `output/` |
| **Notify** | Optional Slack message with TL;DR bullets + links (add `SLACK_WEBHOOK_URL` secret to enable) |

---

## File Structure

```
05-competitive-intel/
├── system/
│   ├── data/
│   │   ├── company-a.md          ← Your company profile (edit this)
│   │   └── competitor-urls.yml   ← Competitor sources config (edit this)
│   ├── scripts/
│   │   ├── run.py                ← Orchestrator
│   │   ├── scrape.py             ← Firecrawl REST API calls
│   │   ├── analyze.py            ← Claude API: battlecard + changelog
│   │   ├── render.py             ← HTML (markdown lib) + PDF (WeasyPrint)
│   │   └── notify.py             ← Slack webhook notification
│   └── requirements.txt
└── output/
    ├── battlecard.md             ← Source-of-truth battlecard (Markdown)
    ├── battlecard.html           ← Styled HTML version
    ├── battlecard.pdf            ← Designed PDF — shareable artifact
    ├── changelog.md              ← Append-only log of changes per run
    └── snapshots/
        └── YYYY-MM-DD/
            └── competitor-raw.json   ← Raw Firecrawl output (audit trail)
```

The workflow file lives at the repo root: `.github/workflows/competitive-intel.yml`

---

## Configuration

### GitHub Secrets (Settings → Secrets and variables → Actions)

| Secret | Required | Description |
|--------|----------|-------------|
| `FIRECRAWL_API_KEY` | Yes | Firecrawl API key (firecrawl.dev) |
| `ANTHROPIC_API_KEY` | Yes | Anthropic API key (console.anthropic.com) |
| `SLACK_WEBHOOK_URL` | No | Slack incoming webhook URL — omit to skip notifications |

### GitHub Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CLAUDE_MODEL` | `claude-haiku-4-5-20251001` | Claude model to use for analysis |

---

## Your Two Files to Maintain

### `system/data/company-a.md`

Your company profile. Keep it current — this is the only file you edit manually. It drives all ICP framing in the battlecard. Schema:

```markdown
# Company A: [Name]

## ICP Definition
[2-3 sentences: who buys, why, what triggers the purchase]

## Our Positioning
## Pricing & Packaging
## Key Differentiators
## Customer Proof Points
## Known Weaknesses / Objections
```

The `## ICP Definition` section is extracted separately and placed at the top of the Claude prompt. Make it specific — it frames every "ICP Perception" paragraph in the battlecard.

### `system/data/competitor-urls.yml`

Defines which URLs to scrape. Add, remove, or change sources here without touching any code.

```yaml
competitor_name: "CompanyB"

urls:
  pricing:
    url: "https://companyb.com/pricing"
    label: "Pricing Page"
  blog:
    url: "https://companyb.com/blog"
    label: "Blog"
  g2:
    url: "https://www.g2.com/products/companyb/reviews"
    label: "G2 Profile"
```

---

## Triggering Runs

**Scheduled:** Every Monday 9am UTC automatically.

**Ad-hoc via GitHub UI:** Actions → Competitive Intelligence → Run workflow → enter a reason → Run workflow.

**Ad-hoc via CLI:**
```bash
gh workflow run competitive-intel.yml --field reason="competitor launched new pricing"
```

---

## How to Expand

### Add a new competitor

The current system is configured for one competitor at a time. To track multiple competitors, the simplest approach is to duplicate the workflow and data files:

1. Copy `competitor-urls.yml` → `competitor-urls-tidio.yml`, `competitor-urls-intercom.yml`, etc.
2. Duplicate the workflow job (or create separate workflow files) for each competitor, passing a `COMPETITOR_CONFIG` env var pointing to the right yml file
3. Update `run.py` to read `COMPETITOR_CONFIG` from env instead of hardcoding the filename
4. Outputs would go to `output/tidio/`, `output/intercom/`, etc.

### Add more sources per competitor

Just add entries to `competitor-urls.yml` — any URL Firecrawl can scrape works:

```yaml
  linkedin:
    url: "https://www.linkedin.com/company/companyb/"
    label: "LinkedIn"
  capterra:
    url: "https://www.capterra.com/p/companyb/reviews/"
    label: "Capterra"
  changelog:
    url: "https://companyb.com/changelog"
    label: "Product Changelog"
```

### Upgrade the AI model

Change the `CLAUDE_MODEL` GitHub Variable to `claude-sonnet-4-6` for higher-quality analysis (~$5/year vs ~$1.30/year). No code changes needed.

### Enable Slack notifications

Add `SLACK_WEBHOOK_URL` as a GitHub Secret (Settings → Secrets → New). The notification sends the TL;DR bullets and links to the battlecard PDF and changelog. No code changes needed.

### Change the battlecard design

Edit the `CSS` constant in `system/scripts/render.py`. It's plain inline CSS — change colours, fonts, layout. The `generate_html()` function handles section-specific styling (TL;DR highlight box, colour-coded Strategic Implications).

### Change the run schedule

Edit `.github/workflows/competitive-intel.yml`, line:
```yaml
- cron: '0 9 * * 1'   # Every Monday 9am UTC
```
Standard cron syntax. Use [crontab.guru](https://crontab.guru) to build expressions.

### Store outputs somewhere other than GitHub

Replace the "Commit and push results" step in the workflow with a step that uploads to S3, Notion, Google Drive, etc. The output files are written to `05-competitive-intel/output/` on the runner before the commit step, so any upload tool can access them there.

---

## Cost

| Item | Cost |
|------|------|
| GitHub Actions | ~5 min/run × 52 weeks. Free tier covers this entirely. |
| Firecrawl | ~5 URLs × 52 runs = 260 credits/year. Free tier = 500/month. |
| Claude (Haiku) | ~$0.025/run → **~$1.30/year** |
| Claude (Sonnet, optional upgrade) | ~$0.09/run → **~$4.70/year** |

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| Scraping returns `[No content returned]` | URL is paywalled or JS-heavy | Try a different URL for the same content |
| `ValueError: Could not find <battlecard_md> block` | Claude response truncated or wrapped in code fences | Both handled automatically — if persists, reduce number of scraped sources |
| PDF not generated | WeasyPrint system deps missing | Workflow installs `libpango` — check Actions log for apt-get errors |
| Workflow doesn't run on schedule | Repo had no activity for 60+ days (GitHub limitation) | Trigger one manual run to reset |
| Slack notification not sent | `SLACK_WEBHOOK_URL` secret not set | Add secret, or ignore — it skips silently |
