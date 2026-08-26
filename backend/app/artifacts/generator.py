"""
Artifact Generation & Extraction Utilities
Extracts structured artifact blocks (Markdown, HTML/CSS) from model outputs.
"""
import re
from typing import Optional, Tuple
from pydantic import BaseModel, Field
from backend.app.artifacts.sanitizer import sanitize_html, sanitize_markdown

class GeneratedArtifact(BaseModel):
    artifact_type: str = Field(..., description="'html' or 'markdown'")
    title: str = Field(...)
    content: str = Field(..., description="Sanitized content for safe rendering")
    raw_content: str = Field(..., description="Raw output from model")


HTML_BLOCK_REGEX = re.compile(r'```(?:html|htm)\s*\n([\s\S]*?)```', re.IGNORECASE)
MARKDOWN_BLOCK_REGEX = re.compile(r'```(?:markdown|md)\s*\n([\s\S]*?)```', re.IGNORECASE)
GENERIC_CODE_BLOCK_REGEX = re.compile(r'```(?:\w+)?\s*\n([\s\S]*?)```', re.IGNORECASE)

def extract_artifact_from_text(text: str, default_title: str = "Growth Artifact") -> GeneratedArtifact:
    """Extract code block or formatted content into a structured artifact."""
    if not text:
        return GeneratedArtifact(
            artifact_type="markdown",
            title=default_title,
            content="Empty artifact",
            raw_content=""
        )

    # 1. Check for explicit HTML code block
    html_match = HTML_BLOCK_REGEX.search(text)
    if html_match:
        raw_code = html_match.group(1).strip()
        title_match = re.search(r'<title[^>]*>(.*?)</title>', raw_code, re.IGNORECASE) or \
                      re.search(r'<h[12][^>]*>(.*?)</h[12]>', raw_code, re.IGNORECASE)
        title = title_match.group(1).strip() if title_match else default_title
        title = re.sub(r'<[^>]+>', '', title)

        sanitized = sanitize_html(raw_code)
        return GeneratedArtifact(
            artifact_type="html",
            title=title,
            content=sanitized,
            raw_content=raw_code
        )

    # 2. Check for explicit Markdown code block
    md_match = MARKDOWN_BLOCK_REGEX.search(text)
    if md_match:
        raw_code = md_match.group(1).strip()
        first_line = raw_code.split("\n")[0]
        title = first_line.replace("#", "").strip() if first_line.startswith("#") else default_title
        sanitized = sanitize_markdown(raw_code)
        return GeneratedArtifact(
            artifact_type="markdown",
            title=title,
            content=sanitized,
            raw_content=raw_code
        )

    # 3. Check for generic code block containing HTML tags
    for code_match in GENERIC_CODE_BLOCK_REGEX.finditer(text):
        raw_code = code_match.group(1).strip()
        if "<!doctype" in raw_code.lower() or "<html" in raw_code.lower() or ("<div" in raw_code.lower() and "<style" in raw_code.lower()):
            title_match = re.search(r'<title[^>]*>(.*?)</title>', raw_code, re.IGNORECASE) or \
                          re.search(r'<h[12][^>]*>(.*?)</h[12]>', raw_code, re.IGNORECASE)
            title = title_match.group(1).strip() if title_match else default_title
            title = re.sub(r'<[^>]+>', '', title)
            sanitized = sanitize_html(raw_code)
            return GeneratedArtifact(
                artifact_type="html",
                title=title,
                content=sanitized,
                raw_content=raw_code
            )

    # 4. Check if text contains full HTML markup directly
    if "<!doctype" in text.lower() or "<html" in text.lower():
        title_match = re.search(r'<title[^>]*>(.*?)</title>', text, re.IGNORECASE) or \
                      re.search(r'<h[12][^>]*>(.*?)</h[12]>', text, re.IGNORECASE)
        title = title_match.group(1).strip() if title_match else default_title
        return GeneratedArtifact(
            artifact_type="html",
            title=title,
            content=sanitize_html(text),
            raw_content=text
        )

    # 5. Default to Markdown artifact
    first_line = text.strip().split("\n")[0]
    title = first_line.replace("#", "").strip() if first_line.startswith("#") else default_title
    return GeneratedArtifact(
        artifact_type="markdown",
        title=title,
        content=sanitize_markdown(text),
        raw_content=text
    )
