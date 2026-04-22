"""Document processing pipeline orchestrator.
 
Coordinates the async pipeline: status update → file read → content extraction →
chunking → embedding generation → chunk storage → status finalization.

The pipeline runs in a separate subprocess to avoid blocking the main uvicorn
event loop and starving other API requests.
"""
 
from __future__ import annotations
 
import asyncio
import multiprocessing
import uuid
from datetime import datetime
from typing import TYPE_CHECKING
 
from BE.core.content_extractor import ContentExtractorFactory
from BE.models.database import Chat, Document, DocumentChunk
from BE.models.enums import FileType
from BE.auth.context import get_current_user
from BE.utils.logger import get_logger
 
if TYPE_CHECKING:
    from BE.client.databricks_llm_client import DatabricksLLMClient
    from BE.client.unity_catalog_client import UnityCatalogClient
    from BE.client.vector_search_client import VectorSearchClient
    from BE.core.chunking_engine import ChunkingEngine
    from BE.core.embedding_generator import EmbeddingGenerator
    from BE.repositories.chat_repository import ChatRepository
    from BE.repositories.chunk_repository import ChunkRepository
    from BE.repositories.document_repository import DocumentRepository
 
logger = get_logger(__name__)


def _run_pipeline_in_subprocess(
    document_id: str,
    storage_path: str,
    file_type: str,
    file_name: str,
    chat_id: str,
) -> None:
    """Standalone function that runs in a separate process.

    Bootstraps its own DB session and clients, then executes the full
    document processing pipeline. This keeps the main uvicorn process
    free to handle API requests.
    """
    _logger = get_logger("document_processor.subprocess")
    trace_id = str(uuid.uuid4())

    try:
        # Bootstrap dependencies inside the subprocess
        from BE.services.dependencies import _get_session_factory
        from BE.client.unity_catalog_client import UnityCatalogClient
        from BE.client.databricks_llm_client import DatabricksLLMClient
        from BE.client.vector_search_client import VectorSearchClient
        from BE.core.chunking_engine import ChunkingEngine
        from BE.core.embedding_generator import EmbeddingGenerator
        from BE.settings import get_settings

        settings = get_settings()
        session = _get_session_factory()()
        uc_client = UnityCatalogClient()
        llm_client = DatabricksLLMClient()
        vs_client = VectorSearchClient()
        embedding_generator = EmbeddingGenerator(llm_client)
        chunking_engine = ChunkingEngine()

        async def _run() -> None:
            nonlocal storage_path, file_type, file_name, chat_id

            # Retry until document is visible in Delta
            for attempt in range(5):
                doc = session.query(Document).filter(
                    Document.document_id == document_id
                ).first()
                if doc is not None:
                    doc.processing_status = "processing"
                    session.commit()
                    storage_path = doc.storage_path or storage_path
                    file_type = doc.file_type or file_type
                    file_name = doc.file_name or file_name
                    chat_id = getattr(doc, "chat_id", "") or chat_id
                    break
                _logger.info(
                    "Document %s not yet visible, retry %d/5",
                    document_id, attempt + 1,
                )
                await asyncio.sleep(3)
                session.expire_all()

            if not storage_path:
                raise ValueError(
                    f"Document {document_id} not found and no metadata provided"
                )

            _logger.info(
                "Starting pipeline for document %s (%s)",
                document_id, file_type,
                extra={"trace_id": trace_id, "document_id": document_id},
            )

            # Read file from Unity Catalog Volume
            file_content = uc_client.read_file(storage_path)

            # Extract content
            ft = FileType(file_type)
            extractor = ContentExtractorFactory.get_extractor(ft, llm_client)
            extracted_contents = await extractor.extract(file_content, file_name)

            # Extract document period from content preview + filename
            import re as _re
            content_preview = file_content[:500].decode("utf-8", errors="replace")
            period_extraction_prompt = (
                f"What time period does this document cover? "
                f"Respond with ONLY the period in one of these formats:\n"
                f"- For quarterly: Q1 2024, Q2 2024, Q3 2024, Q4 2024\n"
                f"- For annual: FY 2024\n"
                f"- If no period can be determined: UNKNOWN\n"
                f"Respond with nothing else.\n"
                f"Filename: {file_name}\nContent preview: {content_preview}"
            )
            try:
                period_result = await llm_client.invoke_haiku(period_extraction_prompt)
                period_result = period_result.strip()
                # Try to extract quarter + year (e.g., "Q3 2024")
                q_match = _re.search(r'Q([1-4])\s*(19|20)\d{2}', period_result)
                fy_match = _re.search(r'FY\s*(19|20)\d{2}', period_result)
                year_match = _re.search(r'\b(19|20)\d{2}\b', period_result)
                if q_match:
                    document_period = q_match.group(0)
                elif fy_match:
                    document_period = fy_match.group(0)
                elif year_match:
                    document_period = f"FY {year_match.group(0)}"
                else:
                    document_period = "UNKNOWN"
            except Exception:
                document_period = "UNKNOWN"
            _logger.info("Extracted document_period=%s for document %s", document_period, document_id)

            # Chunk
            chunk_results = chunking_engine.chunk(extracted_contents)

            # Inject document_period into each chunk's metadata
            for cr in chunk_results:
                if not cr.metadata:
                    cr.metadata = {}
                cr.metadata["document_period"] = document_period

            # Generate embeddings
            chunk_texts = [cr.chunk_text for cr in chunk_results]
            embeddings = await embedding_generator.generate_batch(chunk_texts)

            # Insert chunks using raw SQL for ARRAY<DOUBLE> compatibility
            from sqlalchemy import text as sa_text
            user = get_current_user()
            now = datetime.utcnow()
            chunks_count = 0
            for cr, embedding in zip(chunk_results, embeddings):
                chunk_id = str(uuid.uuid4())
                embedding_sql = (
                    f"ARRAY({','.join(str(v) for v in embedding)})"
                    if embedding else "NULL"
                )
                metadata_val = (
                    str(cr.metadata).replace("'", "''") if cr.metadata else ""
                )

                insert_sql = sa_text(f"""
                    INSERT INTO deal_document_chunks
                    (chunk_id, document_id, chunk_text, chunk_index, chunk_type,
                     page_number, section_name, embedding, metadata, chat_id,
                     is_active, created_by, created_at, updated_by, updated_at)
                    VALUES (
                        :chunk_id, :document_id, :chunk_text, :chunk_index,
                        :chunk_type, :page_number, :section_name, {embedding_sql},
                        :metadata, :chat_id, :is_active, :created_by, :created_at,
                        :updated_by, :updated_at
                    )
                """)
                session.execute(insert_sql, {
                    "chunk_id": chunk_id,
                    "document_id": document_id,
                    "chunk_text": cr.chunk_text,
                    "chunk_index": cr.chunk_index,
                    "chunk_type": cr.chunk_type,
                    "page_number": cr.page_number,
                    "section_name": cr.section_name,
                    "metadata": metadata_val,
                    "chat_id": chat_id,
                    "is_active": True,
                    "created_by": user,
                    "created_at": now,
                    "updated_by": user,
                    "updated_at": now,
                })
                chunks_count += 1
            session.commit()

            # Sync vector search index
            try:
                vs_client.sync_index()
            except Exception as sync_exc:
                _logger.warning(
                    "Vector search index sync failed: %s", str(sync_exc),
                    extra={"trace_id": trace_id, "document_id": document_id},
                )

            # Compute page_count
            page_numbers = [
                ec.page_number for ec in extracted_contents
                if ec.page_number is not None
            ]
            page_count = max(page_numbers) if page_numbers else None

            # Update document status to ready
            doc = session.query(Document).filter(
                Document.document_id == document_id
            ).first()
            if doc:
                doc.processing_status = "ready"
                if page_count is not None:
                    doc.page_count = page_count
                session.commit()

            # Update chat status
            if chat_id:
                DocumentProcessor._update_chat_status(
                    session, chat_id, document_id, "ready"
                )

            _logger.info(
                "Pipeline completed for document %s: %d chunks, page_count=%s",
                document_id, chunks_count, page_count,
                extra={"trace_id": trace_id, "document_id": document_id},
            )

        asyncio.run(_run())

    except Exception as exc:
        _logger.error(
            "Subprocess pipeline failed for document %s: %s",
            document_id, str(exc), exc_info=True,
            extra={"trace_id": trace_id, "document_id": document_id},
        )
        try:
            from BE.services.dependencies import _get_session_factory
            err_session = _get_session_factory()()
            doc = err_session.query(Document).filter(
                Document.document_id == document_id
            ).first()
            if doc:
                doc.processing_status = "failed"
                err_session.commit()
                if chat_id:
                    DocumentProcessor._update_chat_status(
                        err_session, chat_id, document_id, "failed"
                    )
            err_session.close()
        except Exception:
            _logger.error("Failed to update status to 'failed'", exc_info=True)
 
 
class DocumentProcessor:
    """Orchestrates the async document processing pipeline."""
 
    def __init__(
        self,
        document_repository: DocumentRepository,
        chunk_repository: ChunkRepository,
        unity_catalog_client: UnityCatalogClient,
        llm_client: DatabricksLLMClient,
        embedding_generator: EmbeddingGenerator,
        chunking_engine: ChunkingEngine,
        chat_repository: ChatRepository | None = None,
        vector_search_client: VectorSearchClient | None = None,
    ) -> None:
        self._document_repo = document_repository
        self._chunk_repo = chunk_repository
        self._uc_client = unity_catalog_client
        self._llm_client = llm_client
        self._embedding_generator = embedding_generator
        self._chunking_engine = chunking_engine
        self._chat_repo = chat_repository
        self._vs_client = vector_search_client
 
    def trigger_pipeline(
        self,
        document_id: str,
        storage_path: str = "",
        file_type: str = "",
        file_name: str = "",
        chat_id: str = "",
    ) -> None:
        """Dispatch document processing in a separate subprocess.

        Spawns a new process so the main uvicorn event loop stays free
        to handle other API requests while the heavy pipeline runs.
        """
        process = multiprocessing.Process(
            target=_run_pipeline_in_subprocess,
            args=(document_id, storage_path, file_type, file_name, chat_id),
            daemon=True,
        )
        process.start()
        logger.info(
            "Spawned subprocess (pid=%s) for document %s pipeline",
            process.pid, document_id,
        )
 
    async def process_document(
        self,
        document_id: str,
        storage_path: str = "",
        file_type: str = "",
        file_name: str = "",
        chat_id: str = "",
    ) -> None:
        """Execute the full async document processing pipeline.
 
        Uses passed-in metadata to avoid Delta table read consistency issues.
        Creates a fresh DB session for writes.
        """
        from BE.services.dependencies import _get_session_factory
 
        trace_id = str(uuid.uuid4())
        session = _get_session_factory()()
 
        try:
            # Try to update status in DB (may fail if record not yet visible)
            for attempt in range(5):
                doc = session.query(Document).filter(Document.document_id == document_id).first()
                if doc is not None:
                    doc.processing_status = "processing"
                    session.commit()
                    # Use DB values if available
                    storage_path = doc.storage_path or storage_path
                    file_type = doc.file_type or file_type
                    file_name = doc.file_name or file_name
                    chat_id = getattr(doc, "chat_id", "") or chat_id
                    break
                logger.info("Document %s not yet visible, retry %d/5", document_id, attempt + 1)
                await asyncio.sleep(3)
                session.expire_all()
 
            if not storage_path:
                raise ValueError(f"Document {document_id} not found and no metadata provided")
 
            logger.info(
                "Starting pipeline for document %s (%s)",
                document_id, file_type,
                extra={"trace_id": trace_id, "document_id": document_id},
            )
 
            # Read file from Unity Catalog Volume
            file_content = self._uc_client.read_file(storage_path)
 
            # Extract content
            ft = FileType(file_type)
            extractor = ContentExtractorFactory.get_extractor(ft, self._llm_client)
            extracted_contents = await extractor.extract(file_content, file_name)
 
            # Chunk
            chunk_results = self._chunking_engine.chunk(extracted_contents)

            # Extract document period from content preview + filename
            import re as _re
            content_preview_str = file_content[:500].decode("utf-8", errors="replace")
            period_extraction_prompt = (
                f"What time period does this document cover? "
                f"Respond with ONLY the period in one of these formats:\n"
                f"- For quarterly: Q1 2024, Q2 2024, Q3 2024, Q4 2024\n"
                f"- For annual: FY 2024\n"
                f"- If no period can be determined: UNKNOWN\n"
                f"Respond with nothing else.\n"
                f"Filename: {file_name}\nContent preview: {content_preview_str}"
            )
            try:
                period_result = await self._llm_client.invoke_haiku(period_extraction_prompt)
                period_result = period_result.strip()
                q_match = _re.search(r'Q([1-4])\s*(19|20)\d{2}', period_result)
                fy_match = _re.search(r'FY\s*(19|20)\d{2}', period_result)
                year_match = _re.search(r'\b(19|20)\d{2}\b', period_result)
                if q_match:
                    document_period = q_match.group(0)
                elif fy_match:
                    document_period = fy_match.group(0)
                elif year_match:
                    document_period = f"FY {year_match.group(0)}"
                else:
                    document_period = "UNKNOWN"
            except Exception:
                document_period = "UNKNOWN"
            logger.info("Extracted document_period=%s for document %s", document_period, document_id)

            # Inject document_period into each chunk's metadata
            for cr in chunk_results:
                if not cr.metadata:
                    cr.metadata = {}
                cr.metadata["document_period"] = document_period

            # Generate embeddings
            chunk_texts = [cr.chunk_text for cr in chunk_results]
            embeddings = await self._embedding_generator.generate_batch(chunk_texts)
 
            # Create and insert chunks using raw SQL for ARRAY<DOUBLE> compatibility
            from sqlalchemy import text as sa_text
            user = get_current_user()
            now = datetime.utcnow()
            chunks_count = 0
            for cr, embedding in zip(chunk_results, embeddings):
                chunk_id = str(uuid.uuid4())
                embedding_sql = f"ARRAY({','.join(str(v) for v in embedding)})" if embedding else "NULL"
                metadata_val = str(cr.metadata).replace("'", "''") if cr.metadata else ""
 
                insert_sql = sa_text(f"""
                    INSERT INTO deal_document_chunks
                    (chunk_id, document_id, chunk_text, chunk_index, chunk_type,
                     page_number, section_name, embedding, metadata, chat_id,
                     is_active, created_by, created_at, updated_by, updated_at)
                    VALUES (
                        :chunk_id, :document_id, :chunk_text, :chunk_index, :chunk_type,
                        :page_number, :section_name, {embedding_sql}, :metadata, :chat_id,
                        :is_active, :created_by, :created_at, :updated_by, :updated_at
                    )
                """)
                session.execute(insert_sql, {
                    "chunk_id": chunk_id,
                    "document_id": document_id,
                    "chunk_text": cr.chunk_text,
                    "chunk_index": cr.chunk_index,
                    "chunk_type": cr.chunk_type,
                    "page_number": cr.page_number,
                    "section_name": cr.section_name,
                    "metadata": metadata_val,
                    "chat_id": chat_id,
                    "is_active": True,
                    "created_by": user,
                    "created_at": now,
                    "updated_by": user,
                    "updated_at": now,
                })
                chunks_count += 1
            session.commit()
 
            # Sync vector search index
            if self._vs_client is not None:
                try:
                    self._vs_client.sync_index()
                except Exception as sync_exc:
                    logger.warning(
                        "Vector search index sync failed: %s", str(sync_exc),
                        extra={"trace_id": trace_id, "document_id": document_id},
                    )
 
            # Compute page_count
            page_numbers = [ec.page_number for ec in extracted_contents if ec.page_number is not None]
            page_count = max(page_numbers) if page_numbers else None
 
            # Update document status to ready
            doc = session.query(Document).filter(Document.document_id == document_id).first()
            if doc:
                doc.processing_status = "ready"
                if page_count is not None:
                    doc.page_count = page_count
                session.commit()
 
            # Update chat status — pass document_id and its known final status
            # directly to avoid re-reading from Delta (eventual consistency lag)
            if chat_id:
                self._update_chat_status(session, chat_id, document_id, "ready")
 
            logger.info(
                "Pipeline completed for document %s: %d chunks, page_count=%s",
                document_id, chunks_count, page_count,
                extra={"trace_id": trace_id, "document_id": document_id},
            )
 
        except Exception as exc:
            logger.error(
                "Pipeline failed for document %s: %s",
                document_id, str(exc), exc_info=True,
                extra={"trace_id": trace_id, "document_id": document_id},
            )
            try:
                doc = session.query(Document).filter(Document.document_id == document_id).first()
                if doc:
                    doc.processing_status = "failed"
                    session.commit()
                    if chat_id:
                        self._update_chat_status(session, chat_id, document_id, "failed")
            except Exception:
                logger.error("Failed to update status to 'failed'", exc_info=True)
        finally:
            session.close()
 
    @staticmethod
    def _update_chat_status(
        session,
        chat_id: str,
        completed_document_id: str | None = None,
        completed_document_status: str | None = None,
    ) -> None:
        """Update chat status based on all documents' processing states.
 
        To avoid Delta eventual consistency lag, the caller can pass the
        just-committed document_id and its known status. This value is used
        directly instead of re-reading from Delta for that specific document.
        """
        # Expire session cache so other documents are re-fetched fresh
        session.expire_all()
 
        documents = session.query(Document).filter(
            Document.chat_id == chat_id, Document.is_active == True
        ).all()
        if not documents:
            return
 
        # Build status set — override the just-committed document's status
        # directly to avoid Delta eventual consistency lag on re-read
        statuses = set()
        for d in documents:
            if completed_document_id and d.document_id == completed_document_id and completed_document_status:
                statuses.add(completed_document_status)
            else:
                statuses.add(d.processing_status)
 
        if "pending" in statuses or "processing" in statuses:
            new_status = "in_progress"
        elif statuses == {"ready"}:
            new_status = "completed"
        elif "failed" in statuses:
            new_status = "failed"
        else:
            new_status = "in_progress"
 
        chat = session.query(Chat).filter(Chat.chat_id == chat_id, Chat.is_active == True).first()
        if chat and chat.status != new_status:
            chat.status = new_status
            chat.updated_at = datetime.utcnow()
            session.commit()
            logger.info("Chat %s status updated to %s", chat_id, new_status)