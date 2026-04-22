from pathlib import Path

import markdown as md


CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }

body {
    font-family: system-ui, -apple-system, 'Segoe UI', Arial, sans-serif;
    font-size: 14px;
    line-height: 1.6;
    color: #333;
    background: #f0f2f5;
    padding: 24px;
}

.card {
    max-width: 900px;
    margin: 0 auto;
    background: #fff;
    border-radius: 8px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.10);
    padding: 40px 48px;
}

h1 {
    font-size: 22px;
    color: #1a2744;
    border-bottom: 3px solid #1a2744;
    padding-bottom: 10px;
    margin-bottom: 6px;
}

h1 + p {
    font-size: 12px;
    color: #666;
    margin-bottom: 28px;
}

h2 {
    font-size: 15px;
    color: #1a2744;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-top: 32px;
    margin-bottom: 10px;
    padding-bottom: 4px;
    border-bottom: 1px solid #dde3ee;
}

h3 {
    font-size: 13px;
    color: #1a2744;
    margin-top: 14px;
    margin-bottom: 6px;
}

p { margin-bottom: 10px; }

ul, ol { margin: 8px 0 10px 20px; }
li { margin-bottom: 4px; }

.tldr {
    background: #eef4ff;
    border-left: 4px solid #1a2744;
    border-radius: 4px;
    padding: 14px 18px 14px 18px;
    margin: 10px 0 16px;
}

.tldr li { margin-bottom: 6px; }

table {
    width: 100%;
    border-collapse: collapse;
    margin: 12px 0 16px;
    font-size: 13px;
}

th {
    background: #1a2744;
    color: #fff;
    padding: 8px 12px;
    text-align: left;
    font-weight: 600;
}

td {
    padding: 7px 12px;
    border-bottom: 1px solid #e8edf5;
}

tr:nth-child(even) td { background: #f5f7fb; }

.win-section {
    background: #f0faf0;
    border-left: 4px solid #2e7d32;
    border-radius: 4px;
    padding: 12px 16px;
    margin: 8px 0;
}

.vuln-section {
    background: #fffbf0;
    border-left: 4px solid #e65100;
    border-radius: 4px;
    padding: 12px 16px;
    margin: 8px 0;
}

.moves-section {
    background: #f5f0ff;
    border-left: 4px solid #5e35b1;
    border-radius: 4px;
    padding: 12px 16px;
    margin: 8px 0;
}

strong { color: #1a2744; }

blockquote {
    border-left: 3px solid #ccc;
    margin: 8px 0;
    padding: 4px 12px;
    color: #555;
}
"""


def generate_html(battlecard_md: str, competitor_name: str, today: str) -> str:
    """Convert battlecard markdown to a styled standalone HTML document."""
    # Wrap TL;DR list in a styled div before converting
    tldr_marker = "## TL;DR (For the Rep in a Hurry)"
    if tldr_marker in battlecard_md:
        # Find the TL;DR section and wrap its content
        parts = battlecard_md.split(tldr_marker, 1)
        after = parts[1]
        # Find where the next ## section starts
        next_section = after.find("\n## ")
        if next_section != -1:
            tldr_content = after[:next_section]
            rest = after[next_section:]
            battlecard_md = (
                parts[0]
                + tldr_marker
                + "\n<div class='tldr'>"
                + tldr_content
                + "\n</div>"
                + rest
            )

    body = md.markdown(
        battlecard_md,
        extensions=["tables", "fenced_code"],
    )

    # Colour-code Strategic Implications subsections
    body = (
        body
        .replace("<h3>Where We Win</h3>", '<h3>Where We Win</h3><div class="win-section">')
        .replace("<h3>Where We're Vulnerable</h3>", '</div><h3>Where We\'re Vulnerable</h3><div class="vuln-section">')
        .replace("<h3>Recommended Moves</h3>", '</div><h3>Recommended Moves</h3><div class="moves-section">')
        .replace("<h2>Objection Handling</h2>", "</div>\n<h2>Objection Handling</h2>")
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Battlecard: Smartsupp vs. {competitor_name} — {today}</title>
<style>{CSS}</style>
</head>
<body>
<div class="card">
{body}
</div>
</body>
</html>"""


def render_pdf(html_path: Path, pdf_path: Path) -> None:
    """Convert an HTML file to PDF using WeasyPrint."""
    try:
        from weasyprint import HTML
        HTML(filename=str(html_path)).write_pdf(str(pdf_path))
        print(f"  PDF written → {pdf_path.name}")
    except ImportError:
        print("  Warning: weasyprint not installed — skipping PDF generation")
    except Exception as e:
        print(f"  Warning: PDF generation failed: {e}")
