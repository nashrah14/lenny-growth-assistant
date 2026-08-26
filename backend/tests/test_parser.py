"""
Unit Tests for Transcript Parser
"""
import pytest
from pathlib import Path
from backend.app.rag.parser import parse_transcript_file, ParsedTranscript

SAMPLE_TRANSCRIPT_CONTENT = """---
guest: Rahul Vohra
title: How Superhuman Built an Engine to Find Product-Market Fit | Rahul Vohra
youtube_url: https://www.youtube.com/watch?v=sample123
publish_date: 2023-01-15
keywords:
  - pmf
  - onboarding
  - pricing
---

# How Superhuman Built an Engine to Find Product-Market Fit | Rahul Vohra

## Transcript

Rahul Vohra (00:00:00):
Product-market fit is the only thing that matters in the early days. We measured it with the 40% rule.

Lenny (00:00:45):
Welcome to Lenny's Podcast. Today Rahul Vohra explains the exact four questions he asked his users.

Rahul Vohra (00:01:10):
The first question is: how would you feel if you could no longer use Superhuman?
"""

def test_parse_transcript_file(tmp_path):
    ep_dir = tmp_path / "rahul-vohra"
    ep_dir.mkdir()
    t_file = ep_dir / "transcript.md"
    t_file.write_text(SAMPLE_TRANSCRIPT_CONTENT, encoding="utf-8")

    parsed = parse_transcript_file(t_file)
    assert parsed.folder_name == "rahul-vohra"
    assert parsed.guest == "Rahul Vohra"
    assert "Superhuman" in parsed.title
    assert parsed.youtube_url == "https://www.youtube.com/watch?v=sample123"
    assert len(parsed.turns) == 3
    assert parsed.turns[0].speaker == "Rahul Vohra"
    assert "40% rule" in parsed.turns[0].text
    assert parsed.turns[1].speaker == "Lenny"
