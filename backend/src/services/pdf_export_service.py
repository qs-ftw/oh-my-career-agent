"""PDF export service using Playwright for ATS-friendly resume rendering."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger(__name__)

_TEMPLATE_DIR = Path(__file__).parent.parent / "templates"


def normalize_text_for_ats(text: str) -> str:
    """Normalize text for ATS compatibility.

    Replaces special characters that ATS systems may not handle correctly.
    """
    return (
        text.replace("\u2014", "-")   # em dash
        .replace("\u2013", "-")       # en dash
        .replace("\u201c", '"')       # left double quote
        .replace("\u201d", '"')       # right double quote
        .replace("\u2018", "'")       # left single quote
        .replace("\u2019", "'")       # right single quote
        .replace("\u00a0", " ")       # non-breaking space
        .replace("\u200b", "")        # zero-width space
        .replace("\u200c", "")        # zero-width non-joiner
        .replace("\u200d", "")        # zero-width joiner
        .replace("\ufeff", "")        # BOM
    )


def _normalize_content(content: dict) -> dict:
    """Recursively normalize all string values in a content dict."""
    result = {}
    for key, value in content.items():
        if isinstance(value, str):
            result[key] = normalize_text_for_ats(value)
        elif isinstance(value, list):
            result[key] = [
                normalize_text_for_ats(v) if isinstance(v, str)
                else _normalize_content(v) if isinstance(v, dict)
                else v
                for v in value
            ]
        elif isinstance(value, dict):
            result[key] = _normalize_content(value)
        else:
            result[key] = value
    return result


async def render_resume_pdf(content: dict, headline: str = "Resume") -> bytes:
    """Render a resume content dict as a PDF using Playwright.

    Args:
        content: ResumeContent as a dict (summary, skills, experiences, etc.)
        headline: Document headline / candidate name

    Returns:
        PDF bytes
    """
    # Normalize for ATS
    normalized = _normalize_content(content)

    # Render HTML template
    env = Environment(loader=FileSystemLoader(str(_TEMPLATE_DIR)))
    template = env.get_template("resume_export.html")

    # Ensure all expected fields exist
    template_data = {
        "headline": normalize_text_for_ats(headline),
        "contact": normalized.get("contact", {}),
        "summary": normalized.get("summary", ""),
        "skills": normalized.get("skills", []),
        "experiences": normalized.get("experiences", []),
        "projects": normalized.get("projects", []),
        "highlights": normalized.get("highlights", []),
        "metrics": normalized.get("metrics", []),
    }

    html_content = template.render(**template_data)

    # Render PDF with Playwright
    try:
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.set_content(html_content, wait_until="networkidle")
            pdf_bytes = await page.pdf(
                format="A4",
                margin={"top": "20mm", "bottom": "20mm", "left": "15mm", "right": "15mm"},
                print_background=True,
            )
            await browser.close()
            return pdf_bytes
    except ImportError:
        logger.warning("Playwright not installed, falling back to HTML export")
        raise RuntimeError(
            "Playwright is required for PDF export. Install with: pip install playwright && playwright install chromium"
        )
