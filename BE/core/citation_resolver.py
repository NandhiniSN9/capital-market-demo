"""Citation resolver for matching inline citations to retrieved document chunks."""

from __future__ import annotations

import re
from dataclasses import dataclass

from BE.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ResolvedCitation:
    """A citation matched to a specific document chunk."""

    document_id: str
    chunk_id: str
    page_number: int | None = None
    section_name: str | None = None
    source_text: str | None = None
    document_name: str | None = None


# Matches patterns like [Document Name, page 3], [Document Name, p.3], [Document Name, p. 3]
_CITATION_PATTERN = re.compile(
    r"\[([^,\]]+),\s*(?:page\s*|p\.\s*)(\d+)\]",
    re.IGNORECASE,
)


class CitationResolver:
    """Parses inline citations from agent response text and resolves them to chunks."""

    def resolve(
        self,
        raw_response_content: str,
        retrieved_chunks: list[dict],
    ) -> list[ResolvedCitation]:
        """Parse inline citations and match them to retrieved chunks.

        Citation format: ``[Document Name, page X]`` or ``[Document Name, p.X]``

        For each citation found, attempts to match by document_name and page_number
        against the retrieved_chunks list. If a match is found, a ResolvedCitation
        is created with the chunk's metadata.

        Args:
            raw_response_content: The raw text response from the agent.
            retrieved_chunks: List of dicts with keys: chunk_id, chunk_text,
                document_id, document_name, page_number, section_name, chunk_type.

        Returns:
            A list of ResolvedCitation instances for matched citations.
        """
        matches = _CITATION_PATTERN.findall(raw_response_content)
        if not matches:
            return []

        resolved: list[ResolvedCitation] = []
        seen: set[tuple[str, int]] = set()

        for doc_name_raw, page_str in matches:
            doc_name = doc_name_raw.strip()
            page_num = int(page_str)

            # Deduplicate identical citations
            key = (doc_name.lower(), page_num)
            if key in seen:
                continue
            seen.add(key)

            # Find best matching chunk
            best_chunk = self._find_matching_chunk(doc_name, page_num, retrieved_chunks)
            if best_chunk is not None:
                resolved.append(
                    ResolvedCitation(
                        document_id=best_chunk.get("document_id", ""),
                        chunk_id=best_chunk.get("chunk_id", ""),
                        page_number=best_chunk.get("page_number"),
                        section_name=best_chunk.get("section_name"),
                        source_text=best_chunk.get("chunk_text"),
                        document_name=best_chunk.get("document_name", doc_name),
                    )
                )
            else:
                logger.warning(
                    "Could not resolve citation: [%s, page %d]",
                    doc_name,
                    page_num,
                )

        return resolved

    @staticmethod
    def _find_matching_chunk(
        doc_name: str,
        page_number: int,
        chunks: list[dict],
    ) -> dict | None:
        """Find the best matching chunk by document_name and page_number.

        Matching priority:
        1. Exact document_name match + exact page_number match
        2. Partial document_name match (case-insensitive contains) + exact page_number
        3. Exact document_name match (any page)
        """
        doc_name_lower = doc_name.lower()

        # Priority 1: exact name + exact page
        for chunk in chunks:
            chunk_doc_name = (chunk.get("document_name") or "").lower()
            chunk_page = chunk.get("page_number")
            if chunk_doc_name == doc_name_lower and chunk_page == page_number:
                return chunk

        # Priority 2: partial name match + exact page
        for chunk in chunks:
            chunk_doc_name = (chunk.get("document_name") or "").lower()
            chunk_page = chunk.get("page_number")
            if doc_name_lower in chunk_doc_name and chunk_page == page_number:
                return chunk

        # Priority 3: exact name match, any page
        for chunk in chunks:
            chunk_doc_name = (chunk.get("document_name") or "").lower()
            if chunk_doc_name == doc_name_lower:
                return chunk

        return None
