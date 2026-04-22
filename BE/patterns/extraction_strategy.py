"""Strategy pattern for document content extraction."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ExtractedContent:
    """Unified representation of content extracted from a document."""

    chunk_text: str
    page_number: int | None = None
    section_name: str | None = None
    chunk_type: str = "text"
    metadata: dict = field(default_factory=dict)


class ContentExtractor(ABC):
    """Abstract base class for document content extractors."""

    @abstractmethod
    async def extract(self, file_content: bytes, file_name: str) -> list[ExtractedContent]:
        """Extract content from a file.

        Args:
            file_content: Raw bytes of the file.
            file_name: Original file name (used for logging/context).

        Returns:
            A list of extracted content items.
        """
