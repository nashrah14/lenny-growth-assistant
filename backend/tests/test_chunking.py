"""
Unit Tests for Semantic Chunker
"""
import pytest
from backend.app.rag.parser import ParsedTranscript, SpeakerTurn
from backend.app.rag.chunking import TranscriptChunker, create_deterministic_chunk_id

def test_deterministic_chunk_id():
    id1 = create_deterministic_chunk_id("rahul-vohra", 0)
    id2 = create_deterministic_chunk_id("rahul-vohra", 0)
    id3 = create_deterministic_chunk_id("rahul-vohra", 1)
    assert id1 == id2
    assert id1 != id3

def test_chunk_transcript():
    transcript = ParsedTranscript(
        document_id="elena-verna",
        folder_name="elena-verna",
        title="B2B PLG Loops",
        guest="Elena Verna",
        youtube_url="https://youtube.com/sample",
        keywords=["plg", "loops"],
        raw_content="",
        clean_text="",
        turns=[
            SpeakerTurn(speaker="Elena Verna", timestamp="00:00:10", text="PLG is an acquisition and retention engine. " * 10),
            SpeakerTurn(speaker="Lenny", timestamp="00:02:00", text="How do you convince enterprise sales? " * 5),
            SpeakerTurn(speaker="Elena Verna", timestamp="00:03:30", text="Product-led sales layers on top of usage. " * 8)
        ]
    )

    chunker = TranscriptChunker(chunk_size=400, chunk_overlap=80)
    chunks = chunker.chunk_transcript(transcript)

    assert len(chunks) >= 2
    for c in chunks:
        assert c.document_id == "elena-verna"
        assert c.episode_title == "B2B PLG Loops"
        assert len(c.text) > 0
        assert c.chunk_id is not None
