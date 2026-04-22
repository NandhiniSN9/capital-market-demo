"""Embedding generation via Databricks Foundation Models (BGE-large)."""

from __future__ import annotations

from BE.client.databricks_llm_client import DatabricksLLMClient
from BE.utils.logger import get_logger

logger = get_logger(__name__)


class EmbeddingGenerator:
    """Generates 1024-dimension embedding vectors using the configured embedding endpoint."""

    def __init__(self, llm_client: DatabricksLLMClient) -> None:
        self._llm_client = llm_client

    async def generate(self, text: str) -> list[float]:
        """Generate an embedding vector for a single text string.

        Returns:
            A list of floats representing the 1024-dimension embedding.
        """
        return await self._llm_client.generate_embedding(text)

    async def generate_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a batch of texts.

        Calls ``generate`` for each text sequentially to stay within
        endpoint rate limits.

        Returns:
            A list of embedding vectors, one per input text.
        """
        embeddings: list[list[float]] = []
        for text in texts:
            embedding = await self.generate(text)
            embeddings.append(embedding)
        return embeddings
