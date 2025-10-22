from collections.abc import Iterable
from typing import List


def chunk_transcript(
    segments: Iterable[dict],
    max_chars: int = 800,
    overlap: int = 120,
) -> List[str]:
    """
    Simple text chunker that concatenates transcript segments until max_chars is reached.
    Adds overlap to smooth retrieval boundaries.
    """
    chunks: List[str] = []
    buffer = ""
    for segment in segments:
        text = segment.get("text", "")
        if not text:
            continue
        if len(buffer) + len(text) > max_chars and buffer:
            chunks.append(buffer.strip())
            buffer = buffer[-overlap:] if overlap < len(buffer) else buffer
        buffer += f" {text}"
    if buffer.strip():
        chunks.append(buffer.strip())
    return chunks
