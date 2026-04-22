"""Hybrid chunking engine: section-based splitting with fixed-size fallback."""

from __future__ import annotations

from dataclasses import dataclass, field

import tiktoken

from BE.patterns.extraction_strategy import ExtractedContent
from BE.settings import CHUNK_OVERLAP_TOKENS, MAX_CHUNK_TOKENS
from BE.utils.logger import get_logger

logger = get_logger(__name__)

_ENCODING = tiktoken.get_encoding("cl100k_base")


@dataclass
class ChunkResult:
    """A single chunk produced by the chunking engine."""

    chunk_text: str
    chunk_index: int
    chunk_type: str
    page_number: int | None = None
    section_name: str | None = None
    metadata: dict = field(default_factory=dict)


class ChunkingEngine:
    """Splits extracted content into token-bounded chunks.

    Strategy:
    - Tables and charts are kept as single chunks (never split).
    - Text content is grouped by section/heading first.
    - Sections exceeding ``MAX_CHUNK_TOKENS`` are split with
      ``CHUNK_OVERLAP_TOKENS`` token overlap.
    """

    def chunk(self, extracted_contents: list[ExtractedContent]) -> list[ChunkResult]:
        """Produce a sequentially-indexed list of chunks."""
        raw_chunks: list[ChunkResult] = []

        for content in extracted_contents:
            if content.chunk_type in ("table", "chart"):
                # Never split tables or chart-extracted text
                raw_chunks.append(
                    ChunkResult(
                        chunk_text=content.chunk_text,
                        chunk_index=0,  # placeholder, assigned below
                        chunk_type=content.chunk_type,
                        page_number=content.page_number,
                        section_name=content.section_name,
                        metadata=dict(content.metadata),
                    )
                )
                continue

            # Text content — apply fixed-size chunking if needed
            token_count = _count_tokens(content.chunk_text)
            if token_count <= MAX_CHUNK_TOKENS:
                raw_chunks.append(
                    ChunkResult(
                        chunk_text=content.chunk_text,
                        chunk_index=0,
                        chunk_type=content.chunk_type,
                        page_number=content.page_number,
                        section_name=content.section_name,
                        metadata=dict(content.metadata),
                    )
                )
            else:
                sub_chunks = _split_text_with_overlap(
                    content.chunk_text,
                    MAX_CHUNK_TOKENS,
                    CHUNK_OVERLAP_TOKENS,
                )
                for sub_text in sub_chunks:
                    raw_chunks.append(
                        ChunkResult(
                            chunk_text=sub_text,
                            chunk_index=0,
                            chunk_type=content.chunk_type,
                            page_number=content.page_number,
                            section_name=content.section_name,
                            metadata=dict(content.metadata),
                        )
                    )

        # Assign sequential chunk_index
        for idx, chunk in enumerate(raw_chunks):
            chunk.chunk_index = idx

        return raw_chunks


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _count_tokens(text: str) -> int:
    """Return the number of tokens in *text* using cl100k_base encoding."""
    return len(_ENCODING.encode(text))


def _split_text_with_overlap(text: str, max_tokens: int, overlap_tokens: int) -> list[str]:
    """Split *text* into chunks of at most *max_tokens* with *overlap_tokens* overlap."""
    tokens = _ENCODING.encode(text)
    chunks: list[str] = []
    start = 0

    while start < len(tokens):
        end = start + max_tokens
        chunk_tokens = tokens[start:end]
        chunks.append(_ENCODING.decode(chunk_tokens))
        # Advance by (max_tokens - overlap) so the next chunk overlaps
        start += max_tokens - overlap_tokens

    return chunks
