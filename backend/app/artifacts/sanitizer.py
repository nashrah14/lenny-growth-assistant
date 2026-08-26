"""
Artifact Security Sanitizer
Provides multi-layer HTML sanitization and CSP injection to neutralize XSS vulnerabilities.
"""
import re
import bleach
from typing import Dict, Any, List
from backend.app.core.logging import logger
from backend.app.core.exceptions import SanitizationError

# Whitelist of safe structural and presentation HTML tags
ALLOWED_TAGS = [
    "html", "head", "body", "meta", "title", "style",
    "div", "span", "p", "h1", "h2", "h3", "h4", "h5", "h6",
    "ul", "ol", "li", "dl", "dt", "dd",
    "table", "thead", "tbody", "tfoot", "tr", "th", "td", "caption",
    "button", "input", "select", "option", "textarea", "label", "fieldset", "legend",
    "svg", "path", "circle", "rect", "line", "polyline", "polygon", "text", "g", "defs",
    "canvas", "section", "article", "header", "footer", "nav", "main", "aside",
    "b", "strong", "i", "em", "u", "s", "strike", "code", "pre", "blockquote", "hr", "br",
    "img", "a", "details", "summary", "progress", "meter"
]

ALLOWED_ATTRIBUTES = {
    "*": ["class", "id", "style", "title", "aria-*", "role", "data-*"],
    "input": ["type", "value", "placeholder", "min", "max", "step", "checked", "disabled", "readonly", "name"],
    "button": ["type", "disabled", "name", "value"],
    "select": ["name", "disabled", "multiple", "size"],
    "option": ["value", "selected", "disabled"],
    "textarea": ["rows", "cols", "placeholder", "disabled", "readonly", "name"],
    "label": ["for"],
    "a": ["href", "target", "rel"],
    "img": ["src", "alt", "width", "height"],
    "table": ["border", "cellpadding", "cellspacing"],
    "td": ["colspan", "rowspan"],
    "th": ["colspan", "rowspan", "scope"],
    "svg": ["viewbox", "width", "height", "fill", "stroke", "xmlns", "version"],
    "path": ["d", "fill", "stroke", "stroke-width", "stroke-linecap", "stroke-linejoin"],
    "circle": ["cx", "cy", "r", "fill", "stroke"],
    "rect": ["x", "y", "width", "height", "rx", "ry", "fill", "stroke"],
    "line": ["x1", "y1", "x2", "y2", "stroke", "stroke-width"],
    "polyline": ["points", "fill", "stroke"],
    "polygon": ["points", "fill", "stroke"],
    "text": ["x", "y", "fill", "font-size", "text-anchor", "font-family"],
    "meta": ["charset", "name", "content", "http-equiv"]
}

ALLOWED_PROTOCOLS = ["http", "https", "mailto"]

CSP_META_TAG = (
    '<meta http-equiv="Content-Security-Policy" '
    'content="default-src \'none\'; style-src \'unsafe-inline\' https://fonts.googleapis.com; '
    'font-src https://fonts.gstatic.com; img-src data: https:; script-src \'unsafe-inline\';">'
)

def sanitize_html(raw_html: str) -> str:
    """
    Sanitize generated HTML to strip dangerous elements, protocols, and attributes.
    Injects a strict Content Security Policy meta header into the document.
    """
    if not raw_html or not raw_html.strip():
        return "<div class='p-4 text-muted'>Empty artifact</div>"

    # Step 0: Remove <script>, <object>, <embed>, <iframe> blocks completely including inner text
    cleaned = re.sub(r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>', '', raw_html, flags=re.IGNORECASE)
    cleaned = re.sub(r'<object\b[^<]*(?:(?!<\/object>)<[^<]*)*<\/object>', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'<embed\b[^>]*>', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'<iframe\b[^<]*(?:(?!<\/iframe>)<[^<]*)*<\/iframe>', '', cleaned, flags=re.IGNORECASE)

    # Step 1: Bleach clean for allowed structural elements and attributes
    cleaned = bleach.clean(
        cleaned,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
        strip_comments=True
    )

    # Step 2: Remove any residual on* inline event handler patterns (e.g. onclick, onerror, onload)
    cleaned = re.sub(r'\s+on[a-zA-Z]+\s*=\s*(["\']).*?\1', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\s+on[a-zA-Z]+\s*=\s*[^"\'\s>]+', '', cleaned, flags=re.IGNORECASE)

    # Step 3: Remove javascript: pseudo-protocol URIs
    cleaned = re.sub(r'href\s*=\s*(["\'])javascript:.*?\1', 'href="#"', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'src\s*=\s*(["\'])javascript:.*?\1', '', cleaned, flags=re.IGNORECASE)

    # Step 4: Inject CSP header and styling wrapper if full HTML doc or fragment
    if "<head>" in cleaned.lower():
        cleaned = re.sub(r'(<head[^>]*>)', r'\1\n  ' + CSP_META_TAG, cleaned, count=1, flags=re.IGNORECASE)
    elif "<html" in cleaned.lower():
        cleaned = re.sub(r'(<html[^>]*>)', r'\1\n<head>\n  ' + CSP_META_TAG + '\n</head>', cleaned, count=1, flags=re.IGNORECASE)
    else:
        # Wrap fragment in complete secure HTML document
        cleaned = (
            f"<!DOCTYPE html>\n"
            f"<html lang=\"en\">\n"
            f"<head>\n"
            f"  <meta charset=\"UTF-8\">\n"
            f"  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n"
            f"  {CSP_META_TAG}\n"
            f"  <style>\n"
            f"    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #0F172A; color: #F8FAFC; }}\n"
            f"    input, select, button {{ font-family: inherit; font-size: 14px; }}\n"
            f"    button {{ cursor: pointer; background: #F59E0B; color: #000; border: none; padding: 8px 16px; border-radius: 6px; font-weight: 600; }}\n"
            f"    input, select {{ background: #1E293B; border: 1px solid #334155; color: #fff; padding: 8px 12px; border-radius: 6px; }}\n"
            f"    .card {{ background: #1E293B; border-radius: 8px; padding: 16px; border: 1px solid #334155; margin-bottom: 16px; }}\n"
            f"  </style>\n"
            f"</head>\n"
            f"<body>\n"
            f"{cleaned}\n"
            f"</body>\n"
            f"</html>"
        )

    return cleaned


def sanitize_markdown(raw_markdown: str) -> str:
    """Sanitize Markdown documents by preventing embedded dangerous HTML."""
    if not raw_markdown:
        return ""
    # Strip <script> and dangerous tags inside markdown
    return re.sub(r'<script.*?>.*?</script>', '', raw_markdown, flags=re.DOTALL | re.IGNORECASE)
