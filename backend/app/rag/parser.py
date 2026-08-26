"""
Podcast Transcript Parser
Extracts YAML metadata, speaker turns, timestamps, and normalized text.
"""
import re
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class SpeakerTurn(BaseModel):
    speaker: str = Field(default="Unknown")
    timestamp: str = Field(default="00:00:00")
    text: str = Field(...)


class ParsedTranscript(BaseModel):
    document_id: str
    folder_name: str
    title: str
    guest: Optional[str] = None
    youtube_url: Optional[str] = None
    spotify_url: Optional[str] = None
    publish_date: Optional[str] = None
    duration_seconds: Optional[float] = None
    keywords: List[str] = Field(default_factory=list)
    raw_content: str
    clean_text: str
    turns: List[SpeakerTurn] = Field(default_factory=list)


# Regex for speaker turn: e.g. "Ada Chen Rekhi (00:00:00):" or "Lenny (00:01:23):" or "(00:02:15):"
SPEAKER_TURN_PATTERN = re.compile(
    r'(?:^|\n)(?:([A-Za-z\s\.\'\-]+?)\s*)?\(([\d]{1,2}:[\d]{2}(?::[\d]{2})?)\):\s*\n?(.*?)(?=(?:\n(?:[A-Za-z\s\.\'\-]+?\s*)?\([\d]{1,2}:[\d]{2}(?::[\d]{2})?\):)|\Z)',
    re.DOTALL
)


def parse_transcript_file(file_path: Path) -> ParsedTranscript:
    """Parse a single transcript markdown file with frontmatter and speaker turns."""
    folder_name = file_path.parent.name
    document_id = folder_name

    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    metadata: Dict[str, Any] = {}
    body = content

    # Extract YAML frontmatter
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            try:
                fm = yaml.safe_load(parts[1])
                if isinstance(fm, dict):
                    metadata = fm
                body = parts[2].strip()
            except Exception:
                body = content

    title = metadata.get("title") or folder_name.replace("-", " ").title()
    guest = metadata.get("guest")
    youtube_url = metadata.get("youtube_url")
    spotify_url = metadata.get("spotify_url")
    publish_date = str(metadata.get("publish_date")) if metadata.get("publish_date") else None
    duration_seconds = metadata.get("duration_seconds")
    keywords = metadata.get("keywords") or []
    if isinstance(keywords, str):
        keywords = [k.strip() for k in keywords.split(",")]

    # Remove Markdown headers like "# Title", "## Transcript" from body
    clean_body = re.sub(r'^#+\s+.*$', '', body, flags=re.MULTILINE).strip()

    # Parse speaker turns
    turns: List[SpeakerTurn] = []
    current_speaker = guest or "Guest"

    for match in SPEAKER_TURN_PATTERN.finditer(clean_body):
        spk_raw, timestamp, text = match.groups()
        if spk_raw and spk_raw.strip():
            current_speaker = spk_raw.strip()
        
        turn_text = re.sub(r'\s+', ' ', text).strip()
        if turn_text:
            turns.append(SpeakerTurn(
                speaker=current_speaker,
                timestamp=timestamp.strip(),
                text=turn_text
            ))

    # If no turns matched regex, create single turn
    if not turns and clean_body:
        turns.append(SpeakerTurn(
            speaker=guest or "Lenny & Guest",
            timestamp="00:00:00",
            text=re.sub(r'\s+', ' ', clean_body).strip()
        ))

    return ParsedTranscript(
        document_id=document_id,
        folder_name=folder_name,
        title=title,
        guest=guest,
        youtube_url=youtube_url,
        spotify_url=spotify_url,
        publish_date=publish_date,
        duration_seconds=duration_seconds,
        keywords=keywords,
        raw_content=content,
        clean_text=clean_body,
        turns=turns
    )
