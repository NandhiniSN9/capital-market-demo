"""Dependency injection configuration for Deal Intelligence Agent."""

from __future__ import annotations

from collections.abc import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from BE.client.databricks_llm_client import DatabricksLLMClient
from BE.client.unity_catalog_client import UnityCatalogClient
from BE.client.vector_search_client import VectorSearchClient
from BE.core.chunking_engine import ChunkingEngine
from BE.core.document_processor import DocumentProcessor
from BE.core.embedding_generator import EmbeddingGenerator
from BE.repositories.chat_repository import ChatRepository
from BE.repositories.chunk_repository import ChunkRepository
from BE.repositories.citation_repository import CitationRepository
from BE.repositories.conversation_repository import ConversationRepository
from BE.repositories.document_repository import DocumentRepository
from BE.repositories.message_repository import MessageRepository
from BE.repositories.session_repository import SessionRepository
from BE.services.chat_service import ChatService
from BE.services.conversation_service import ConversationService
from BE.services.document_service import DocumentService
from BE.services.message_service import MessageService
from BE.services.session_service import DealSessionService
from BE.settings import get_settings


# ---------------------------------------------------------------------------
# Database session
# ---------------------------------------------------------------------------


_session_factory: sessionmaker | None = None


def _get_session_factory() -> sessionmaker:
    """Return a cached session factory from the shared db module (handles token refresh)."""
    global _session_factory
    from BE.models.db import get_engine
    from sqlalchemy.orm import sessionmaker

    engine = get_engine()
    # Recreate factory only if engine changed (e.g. token refresh rebuilt it)
    if _session_factory is None or _session_factory.kw.get("bind") is not engine:
        _session_factory = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    return _session_factory


def get_db_session() -> Generator[Session, None, None]:
    factory = _get_session_factory()
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Repository factories
# ---------------------------------------------------------------------------

def get_chat_repository(session: Session = Depends(get_db_session)) -> ChatRepository:
    return ChatRepository(session)

def get_document_repository(session: Session = Depends(get_db_session)) -> DocumentRepository:
    return DocumentRepository(session)

def get_chunk_repository(session: Session = Depends(get_db_session)) -> ChunkRepository:
    return ChunkRepository(session)

def get_session_repository(session: Session = Depends(get_db_session)) -> SessionRepository:
    return SessionRepository(session)

def get_message_repository(session: Session = Depends(get_db_session)) -> MessageRepository:
    return MessageRepository(session)

def get_citation_repository(session: Session = Depends(get_db_session)) -> CitationRepository:
    return CitationRepository(session)

def get_conversation_repository(session: Session = Depends(get_db_session)) -> ConversationRepository:
    return ConversationRepository(session)


# ---------------------------------------------------------------------------
# Client factories (singletons — avoid re-creating WorkspaceClient per request)
# ---------------------------------------------------------------------------

_vector_search_client: VectorSearchClient | None = None
_unity_catalog_client: UnityCatalogClient | None = None
_llm_client: DatabricksLLMClient | None = None


def get_vector_search_client() -> VectorSearchClient:
    global _vector_search_client
    if _vector_search_client is None:
        _vector_search_client = VectorSearchClient(settings=get_settings())
    return _vector_search_client

def get_unity_catalog_client() -> UnityCatalogClient:
    global _unity_catalog_client
    if _unity_catalog_client is None:
        _unity_catalog_client = UnityCatalogClient(settings=get_settings())
    return _unity_catalog_client

def get_llm_client() -> DatabricksLLMClient:
    global _llm_client
    if _llm_client is None:
        _llm_client = DatabricksLLMClient(settings=get_settings())
    return _llm_client


# ---------------------------------------------------------------------------
# Service factories
# ---------------------------------------------------------------------------

def get_document_service(
    session: Session = Depends(get_db_session),
    unity_catalog_client: UnityCatalogClient = Depends(get_unity_catalog_client),
    llm_client: DatabricksLLMClient = Depends(get_llm_client),
    vector_search_client: VectorSearchClient = Depends(get_vector_search_client),
) -> DocumentService:
    document_repository = DocumentRepository(session)
    chunk_repository = ChunkRepository(session)
    citation_repository = CitationRepository(session)
    chat_repository = ChatRepository(session)
    embedding_generator = EmbeddingGenerator(llm_client)
    chunking_engine = ChunkingEngine()
    document_processor = DocumentProcessor(
        document_repository=document_repository,
        chunk_repository=chunk_repository,
        unity_catalog_client=unity_catalog_client,
        llm_client=llm_client,
        embedding_generator=embedding_generator,
        chunking_engine=chunking_engine,
        chat_repository=chat_repository,
        vector_search_client=vector_search_client,
    )
    return DocumentService(
        document_repository=document_repository,
        chunk_repository=chunk_repository,
        citation_repository=citation_repository,
        unity_catalog_client=unity_catalog_client,
        llm_client=llm_client,
        vector_search_client=vector_search_client,
        document_processor=document_processor,
    )


def get_chat_service(
    session: Session = Depends(get_db_session),
    unity_catalog_client: UnityCatalogClient = Depends(get_unity_catalog_client),
    vector_search_client: VectorSearchClient = Depends(get_vector_search_client),
    llm_client: DatabricksLLMClient = Depends(get_llm_client),
) -> ChatService:
    chat_repository = ChatRepository(session)
    document_repository = DocumentRepository(session)
    chunk_repository = ChunkRepository(session)
    citation_repository = CitationRepository(session)
    session_repository = SessionRepository(session)
    message_repository = MessageRepository(session)

    embedding_generator = EmbeddingGenerator(llm_client)
    chunking_engine = ChunkingEngine()
    document_processor = DocumentProcessor(
        document_repository=document_repository,
        chunk_repository=chunk_repository,
        unity_catalog_client=unity_catalog_client,
        llm_client=llm_client,
        embedding_generator=embedding_generator,
        chunking_engine=chunking_engine,
        chat_repository=chat_repository,
        vector_search_client=vector_search_client,
    )
    document_service = DocumentService(
        document_repository=document_repository,
        chunk_repository=chunk_repository,
        citation_repository=citation_repository,
        unity_catalog_client=unity_catalog_client,
        llm_client=llm_client,
        vector_search_client=vector_search_client,
        document_processor=document_processor,
    )
    return ChatService(
        chat_repository=chat_repository,
        document_repository=document_repository,
        document_service=document_service,
        session_repository=session_repository,
        message_repository=message_repository,
        unity_catalog_client=unity_catalog_client,
        vector_search_client=vector_search_client,
        chunk_repository=chunk_repository,
        citation_repository=citation_repository,
    )


def get_session_service(
    chat_repository: ChatRepository = Depends(get_chat_repository),
    session_repository: SessionRepository = Depends(get_session_repository),
    message_repository: MessageRepository = Depends(get_message_repository),
) -> DealSessionService:
    return DealSessionService(
        chat_repository=chat_repository,
        session_repository=session_repository,
        message_repository=message_repository,
    )


def get_message_service(
    chat_repository: ChatRepository = Depends(get_chat_repository),
    session_repository: SessionRepository = Depends(get_session_repository),
    message_repository: MessageRepository = Depends(get_message_repository),
    citation_repository: CitationRepository = Depends(get_citation_repository),
) -> MessageService:
    return MessageService(
        chat_repository=chat_repository,
        session_repository=session_repository,
        message_repository=message_repository,
        citation_repository=citation_repository,
    )


def get_conversation_service(
    session: Session = Depends(get_db_session),
    conversation_repository: ConversationRepository = Depends(get_conversation_repository),
) -> ConversationService:
    return ConversationService(
        chat_repository=ChatRepository(session),
        session_repository=SessionRepository(session),
        message_repository=MessageRepository(session),
        conversation_repository=conversation_repository,
        document_repository=DocumentRepository(session),
        citation_repository=CitationRepository(session),
    )


def get_stream_service(
    session: Session = Depends(get_db_session),
) -> "StreamService":
    from BE.services.stream_service import StreamService
    return StreamService(
        chat_repository=ChatRepository(session),
        session_repository=SessionRepository(session),
        message_repository=MessageRepository(session),
        conversation_repository=ConversationRepository(session),
        document_repository=DocumentRepository(session),
    )
