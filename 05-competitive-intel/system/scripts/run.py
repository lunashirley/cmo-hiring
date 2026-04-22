"""
Orchestrator: scrape → analyze → write outputs → render PDF → notify Slack → done.

Environment variables (set by GitHub Actions workflow):
  SYSTEM_DIR   path to 05-competitive-intel/system
  OUTPUT_DIR   path to 05-competitive-intel/output
  RUN_REASON   "scheduled" | "manual" | custom string
  CLAUDE_MODEL anthropic model id (defaults to haiku)
"""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import yaml

from analyze import analyze
from notify import notify_slack
from render import render_pdf
from scrape import scrape_competitor


def prepend_changelog_entry(changelog_path: Path, entry: str) -> None:
    header = "# Competitive Intelligence Changelog\n"
    existing = changelog_path.read_text(encoding="utf-8") if changelog_path.exists() else header
    after_header = existing[len(header):].lstrip("\n")
    changelog_path.write_text(
        header + "\n" + entry.strip() + "\n\n---\n\n" + after_header,
        encoding="utf-8",
    )


def main() -> None:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    run_reason = os.environ.get("RUN_REASON", "scheduled")

    system_dir = Path(os.environ.get("SYSTEM_DIR", "05-competitive-intel/system"))
    output_dir = Path(os.environ.get("OUTPUT_DIR", "05-competitive-intel/output"))
    snapshots_dir = output_dir / "snapshots" / today

    output_dir.mkdir(parents=True, exist_ok=True)
    snapshots_dir.mkdir(parents=True, exist_ok=True)

    # ── Step 1: Read Company A ────────────────────────────────────────────────
    company_a_path = system_dir / "data" / "company-a.md"
    if not company_a_path.exists():
        sys.exit(f"ERROR: {company_a_path} not found. Fill it in before running.")
    company_a = company_a_path.read_text(encoding="utf-8")
    print("✓ Loaded company-a.md")

    # ── Step 2: Load competitor config ───────────────────────────────────────
    urls_config_path = system_dir / "data" / "competitor-urls.yml"
    if not urls_config_path.exists():
        sys.exit(f"ERROR: {urls_config_path} not found.")
    urls_config = yaml.safe_load(urls_config_path.read_text(encoding="utf-8"))
    competitor_name = urls_config["competitor_name"]
    print(f"✓ Competitor: {competitor_name}")

    # ── Step 3: Load previous battlecard (for change detection) ──────────────
    battlecard_path = output_dir / "battlecard.md"
    previous_battlecard = (
        battlecard_path.read_text(encoding="utf-8")
        if battlecard_path.exists()
        else "NONE"
    )

    # ── Step 4: Scrape ────────────────────────────────────────────────────────
    print("Scraping competitor sources...")
    scraped = scrape_competitor(urls_config)
    (snapshots_dir / "competitor-raw.json").write_text(
        json.dumps(scraped, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"✓ Snapshot saved → output/snapshots/{today}/")

    # ── Step 5: Analyze ───────────────────────────────────────────────────────
    print("Analyzing with Claude...")
    result = analyze(
        company_a=company_a,
        scraped=scraped,
        previous_battlecard=previous_battlecard,
        competitor_name=competitor_name,
        today=today,
        run_reason=run_reason,
    )
    print("✓ Analysis complete")

    # ── Step 6: Write outputs ─────────────────────────────────────────────────
    battlecard_path.write_text(result["battlecard_md"], encoding="utf-8")
    (output_dir / "battlecard.html").write_text(result["battlecard_html"], encoding="utf-8")
    prepend_changelog_entry(output_dir / "changelog.md", result["changelog_entry"])
    print("✓ battlecard.md / battlecard.html / changelog.md written")

    # ── Step 7: Render PDF ────────────────────────────────────────────────────
    print("Rendering PDF...")
    render_pdf(
        html_path=output_dir / "battlecard.html",
        pdf_path=output_dir / "battlecard.pdf",
    )

    # ── Step 8: Notify Slack ──────────────────────────────────────────────────
    print("Sending Slack notification...")
    notify_slack(
        battlecard_md=result["battlecard_md"],
        competitor_name=competitor_name,
        today=today,
        run_reason=run_reason,
    )

    print(f"\n✓ Done — {today} ({run_reason})")


if __name__ == "__main__":
    main()
