import re
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
    overflow: hidden;
}

.card-header {
    background: #1a2744;
    padding: 24px 48px 20px 48px;
}

.card-header h1 {
    font-size: 26px;
    color: #fff;
    font-weight: 700;
    letter-spacing: -0.01em;
    border-bottom: none;
    padding-bottom: 0;
    margin-bottom: 0;
}

.card-header .header-meta {
    font-size: 11px;
    color: rgba(255,255,255,0.65);
    margin-top: 6px;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}

.card-body {
    padding: 32px 48px 40px 48px;
}

h2 {
    font-size: 15px;
    color: #1a2744;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-top: 32px;
    margin-bottom: 10px;
    padding-left: 12px;
    border-left: 4px solid #1a2744;
    border-bottom: none;
}

h3 {
    font-size: 13px;
    color: #1a2744;
    font-weight: 700;
    margin-top: 18px;
    margin-bottom: 6px;
}

p { margin-bottom: 10px; }

ul, ol { margin: 8px 0 10px 20px; }
li { margin-bottom: 4px; }

.tldr {
    background: #1a2744;
    color: #fff;
    border-radius: 4px;
    padding: 16px 20px;
    margin: 12px 0 20px;
    page-break-inside: avoid;
}

.tldr li { margin-bottom: 6px; color: #fff; }
.tldr strong { color: #fff; }
.tldr p { color: #fff; }

.icp-block {
    background: #f9f5ff;
    border-left: 4px solid #7c3aed;
    border-radius: 4px;
    padding: 12px 16px;
    margin: 10px 0 14px;
    page-break-inside: avoid;
}

.icp-label {
    font-size: 9px;
    font-weight: 700;
    color: #7c3aed;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 6px;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin: 12px 0 16px;
    font-size: 13px;
    page-break-inside: avoid;
}

th {
    background: #1a2744;
    color: #fff;
    padding: 9px 12px;
    text-align: left;
    font-weight: 600;
    font-size: 12px;
    letter-spacing: 0.03em;
}

td {
    padding: 8px 12px;
    border-bottom: 1px solid #e8edf5;
    vertical-align: top;
}

tr:nth-child(even) td { background: #f5f7fb; }

.objection-table td:first-child {
    font-weight: 700;
    color: #1a2744;
    width: 35%;
}

.objection-table td:last-child {
    font-weight: 400;
}

.win-section {
    background: #f0faf0;
    border-left: 4px solid #2e7d32;
    border-top: 3px solid #2e7d32;
    border-radius: 4px;
    padding: 12px 16px;
    margin: 8px 0;
    page-break-inside: avoid;
}

.vuln-section {
    background: #fffbf0;
    border-left: 4px solid #e65100;
    border-top: 3px solid #e65100;
    border-radius: 4px;
    padding: 12px 16px;
    margin: 8px 0;
    page-break-inside: avoid;
}

.moves-section {
    background: #f5f0ff;
    border-left: 4px solid #5e35b1;
    border-top: 3px solid #5e35b1;
    border-radius: 4px;
    padding: 12px 16px;
    margin: 8px 0;
    page-break-inside: avoid;
}

strong { color: #1a2744; }

blockquote {
    border-left: 3px solid #ccc;
    margin: 8px 0;
    padding: 4px 12px;
    color: #555;
    font-style: italic;
}
"""


def generate_html(battlecard_md: str, competitor_name: str, today: str) -> str:
    """Convert battlecard markdown to a styled standalone HTML document."""
    # Step 1: Wrap TL;DR list in a styled div before converting
    tldr_marker = "## TL;DR (For the Rep in a Hurry)"
    if tldr_marker in battlecard_md:
        parts = battlecard_md.split(tldr_marker, 1)
        after = parts[1]
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

    # Step 2: Convert Markdown to HTML
    body = md.markdown(battlecard_md, extensions=["tables", "fenced_code"])

    # Step 3: Extract h1 title and metadata paragraph into card-header div
    header_html = ""
    header_match = re.search(r'(<h1>.*?</h1>)\s*(<p>.*?</p>)?', body, re.DOTALL)
    if header_match:
        h1_text = re.sub(r'</?h1>', '', header_match.group(1))
        meta_p = header_match.group(2) or ""
        meta_text = re.sub(r'</?p>', '', meta_p).strip()
        header_html = (
            '<div class="card-header">'
            f'<h1>{h1_text}</h1>'
            + (f'<div class="header-meta">{meta_text}</div>' if meta_text else '')
            + '</div>'
        )
        body = body[:header_match.start()] + body[header_match.end():]

    # Step 4: Colour-code Strategic Implications subsections
    body = (
        body
        .replace("<h3>Where We Win</h3>", '<h3>Where We Win</h3><div class="win-section">')
        .replace("<h3>Where We're Vulnerable</h3>", '</div><h3>Where We\'re Vulnerable</h3><div class="vuln-section">')
        .replace("<h3>Recommended Moves</h3>", '</div><h3>Recommended Moves</h3><div class="moves-section">')
        .replace("<h2>Objection Handling</h2>", "</div>\n<h2>Objection Handling</h2>")
    )

    # Step 5: Wrap ICP Perception bold paragraphs in styled aside blocks
    body = re.sub(
        r'<p><strong>ICP Perception:</strong>(.*?)</p>',
        lambda m: (
            '<div class="icp-block">'
            '<div class="icp-label">\u25c6 ICP VIEW</div>'
            f'<p>{m.group(1).strip()}</p>'
            '</div>'
        ),
        body,
        flags=re.DOTALL,
    )

    # Step 6: Add class to Objection Handling table for bold first column
    body = re.sub(
        r'(<h2>Objection Handling</h2>.*?)(<table)',
        r'\1<table class="objection-table"',
        body,
        count=1,
        flags=re.DOTALL,
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Battlecard: Smartsupp vs. {competitor_name} \u2014 {today}</title>
<style>{CSS}</style>
</head>
<body>
<div class="card">
{header_html}
<div class="card-body">
{body}
</div>
</div>
</body>
</html>"""


def render_pdf(html_path: Path, pdf_path: Path) -> None:
    """Convert an HTML file to PDF using WeasyPrint."""
    try:
        from weasyprint import HTML
        HTML(filename=str(html_path)).write_pdf(str(pdf_path))
        print(f"  PDF written \u2192 {pdf_path.name}")
    except ImportError:
        print("  Warning: weasyprint not installed \u2014 skipping PDF generation")
    except Exception as e:
        print(f"  Warning: PDF generation failed: {e}")
