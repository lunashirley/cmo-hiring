from pathlib import Path


def render_pdf(html_path: Path, pdf_path: Path) -> None:
    try:
        from weasyprint import HTML
        HTML(filename=str(html_path)).write_pdf(str(pdf_path))
        print(f"  PDF written → {pdf_path.name}")
    except ImportError:
        print("  Warning: weasyprint not installed — skipping PDF generation")
    except Exception as e:
        print(f"  Warning: PDF generation failed: {e}")
