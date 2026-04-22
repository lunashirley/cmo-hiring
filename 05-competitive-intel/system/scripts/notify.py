import json
import os
import urllib.request


def _extract_tldr(battlecard_md: str) -> list[str]:
    lines = battlecard_md.split("\n")
    in_tldr = False
    bullets: list[str] = []
    for line in lines:
        if "## TL;DR" in line:
            in_tldr = True
            continue
        if in_tldr:
            if line.startswith("## "):
                break
            stripped = line.strip()
            if stripped and stripped[0] in "-•*":
                bullets.append(stripped.lstrip("-•* ").strip())
    return bullets[:3]


def notify_slack(
    battlecard_md: str,
    competitor_name: str,
    today: str,
    run_reason: str,
) -> None:
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL", "").strip()
    if not webhook_url:
        print("  SLACK_WEBHOOK_URL not set — skipping Slack notification")
        return

    bullets = _extract_tldr(battlecard_md)
    bullet_text = "\n".join(f"• {b}" for b in bullets) or "• See battlecard for details"

    repo = os.environ.get("GITHUB_REPOSITORY", "lunashirley/cmo-hiring")
    base_url = f"https://github.com/{repo}/blob/main/05-competitive-intel/output"

    payload = {
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"Competitive Intel: Company A vs. {competitor_name} — {today}",
                },
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*TL;DR*\n{bullet_text}"},
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"<{base_url}/battlecard.pdf|📄 Battlecard (PDF)>"},
                    {"type": "mrkdwn", "text": f"<{base_url}/changelog.md|📋 Changelog>"},
                ],
            },
            {
                "type": "context",
                "elements": [{"type": "mrkdwn", "text": f"Run type: {run_reason}"}],
            },
        ]
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        webhook_url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status == 200:
                print("  Slack notification sent")
            else:
                print(f"  Warning: Slack returned HTTP {resp.status}")
    except Exception as e:
        print(f"  Warning: Slack notification failed: {e}")
