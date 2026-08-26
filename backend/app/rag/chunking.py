"""
Semantic & Speaker-Aware Text Chunker
Divides parsed podcast transcripts into overlapping chunks preserving speaker context.
"""
import uuid
from typing import List, Optional
from pydantic import BaseModel, Field
from backend.app.rag.parser import ParsedTranscript, SpeakerTurn
from backend.app.core.config import settings

class TranscriptChunk(BaseModel):
    chunk_id: str = Field(..., description="Deterministic unique chunk identifier")
    document_id: str = Field(..., description="Parent transcript identifier")
    chunk_index: int = Field(..., description="0-indexed sequence position")
    episode_title: str = Field(...)
    episode_url: Optional[str] = None
    speaker: str = Field(default="Unknown")
    timestamp: str = Field(default="00:00:00")
    text: str = Field(..., description="Chunk content for embedding and synthesis")
    published_at: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)
    source_type: str = Field(default="podcast_transcript")


def create_deterministic_chunk_id(document_id: str, chunk_index: int) -> str:
    """Generate deterministic UUID5 for a given document and chunk index."""
    namespace = uuid.NAMESPACE_DNS
    name = f"lenny_podcast_{document_id}_{chunk_index}"
    return str(uuid.uuid5(namespace, name))


class TranscriptChunker:
    def __init__(self, chunk_size: Optional[int] = None, chunk_overlap: Optional[int] = None):
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP

    def chunk_transcript(self, transcript: ParsedTranscript) -> List[TranscriptChunk]:
        """Convert a parsed transcript into semantic chunks with metadata."""
        chunks: List[TranscriptChunk] = []
        episode_url = transcript.youtube_url or transcript.spotify_url

        if not transcript.turns:
            # Fallback for plain text without parsed turns
            text = transcript.clean_text
            start = 0
            chunk_idx = 0
            while start < len(text):
                end = min(start + self.chunk_size, len(text))
                # Seek nearest space boundary
                if end < len(text):
                    last_space = text.rfind(' ', start, end)
                    if last_space > start + (self.chunk_size // 2):
                        end = last_space

                chunk_text = text[start:end].strip()
                if chunk_text:
                    chunks.append(TranscriptChunk(
                        chunk_id=create_deterministic_chunk_id(transcript.document_id, chunk_idx),
                        document_id=transcript.document_id,
                        chunk_index=chunk_idx,
                        episode_title=transcript.title,
                        episode_url=episode_url,
                        speaker=transcript.guest or "Lenny Rachitsky",
                        timestamp="00:00:00",
                        text=chunk_text,
                        published_at=transcript.publish_date,
                        keywords=transcript.keywords,
                        source_type="podcast_transcript"
                    ))
                    chunk_idx += 1

                start += max(self.chunk_size - self.chunk_overlap, 1)
            return chunks

        # Turn-based chunking
        current_chunk_turns: List[SpeakerTurn] = []
        current_length = 0
        chunk_idx = 0

        for turn in transcript.turns:
            turn_repr = f"{turn.speaker} ({turn.timestamp}): {turn.text}"
            turn_len = len(turn_repr)

            if current_length + turn_len > self.chunk_size and current_chunk_turns:
                # Flush current chunk
                combined_text = "\n".join(f"{t.speaker} ({t.timestamp}): {t.text}" for t in current_chunk_turns)
                primary_speaker = current_chunk_turns[0].speaker
                primary_timestamp = current_chunk_turns[0].timestamp

                chunks.append(TranscriptChunk(
                    chunk_id=create_deterministic_chunk_id(transcript.document_id, chunk_idx),
                    document_id=transcript.document_id,
                    chunk_index=chunk_idx,
                    episode_title=transcript.title,
                    episode_url=episode_url,
                    speaker=primary_speaker,
                    timestamp=primary_timestamp,
                    text=combined_text,
                    published_at=transcript.publish_date,
                    keywords=transcript.keywords,
                    source_type="podcast_transcript"
                ))
                chunk_idx += 1

                # Maintain overlap with the last turn if feasible
                if len(current_chunk_turns) > 1 and len(f"{current_chunk_turns[-1].speaker} ({current_chunk_turns[-1].timestamp}): {current_chunk_turns[-1].text}") <= self.chunk_overlap:
                    current_chunk_turns = [current_chunk_turns[-1], turn]
                    current_length = sum(len(f"{t.speaker} ({t.timestamp}): {t.text}") for t in current_chunk_turns)
                else:
                    current_chunk_turns = [turn]
                    current_length = turn_len
            else:
                current_chunk_turns.append(turn)
                current_length += turn_len

        # Flush remaining turns
        if current_chunk_turns:
            combined_text = "\n".join(f"{t.speaker} ({t.timestamp}): {t.text}" for t in current_chunk_turns)
            primary_speaker = current_chunk_turns[0].speaker
            primary_timestamp = current_chunk_turns[0].timestamp

            chunks.append(TranscriptChunk(
                chunk_id=create_deterministic_chunk_id(transcript.document_id, chunk_idx),
                document_id=transcript.document_id,
                chunk_index=chunk_idx,
                episode_title=transcript.title,
                episode_url=episode_url,
                speaker=primary_speaker,
                timestamp=primary_timestamp,
                text=combined_text,
                published_at=transcript.publish_date,
                keywords=transcript.keywords,
                source_type="podcast_transcript"
            ))

        return chunks
