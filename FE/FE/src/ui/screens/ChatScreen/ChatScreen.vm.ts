import { useRef, useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import secureStorage from 'react-secure-storage';
import { useChatStore } from '../../../store/chatStore.ts';
import { usePersonaStore } from '../../../store/personaStore.ts';
import { useUIStore } from '../../../store/uiStore.ts';
import { chatListService } from '../../../services/chatservice/chatListServiceSelector.ts';
import { apiClient } from '../../../helpers/apiClient/apiClient.ts';
import { ServiceResultStatusENUM } from '../../../types/service/ServiceResultStatusENUM.ts';
import { ApiDocumentBO } from '../../../types/document/ApiDocumentBO.ts';
import { SessionSummaryBO } from '../../../types/chat/SessionSummaryBO.ts';
import { DocumentDTO } from '../../../services/chatservice/types/CreateChatResponseDTO.ts';
import { SessionSummaryDTO } from '../../../services/chatservice/types/GetChatDetailResponseDTO.ts';
import { ConversationPollResponseDTO } from '../../../services/chatservice/types/ConversationPollResponseDTO.ts';
import { SECURE_STORAGE_KEYS } from '../../../helpers/storage/secureStorageKeys.ts';
import { PERSONA_TO_ANALYST_TYPE } from '../../../helpers/config/analystTypeMap.ts';
import { ScenarioTypeENUM } from '../../../types/chat/ScenarioTypeENUM.ts';
import { AgentTypeENUM } from '../../../types/chat/AgentTypeENUM.ts';
import { streamMessage } from '../../../services/chatservice/streamService.ts';
import { toast } from 'sonner';

const POLL_INTERVAL_MS = 2000;
const MAX_POLL_ATTEMPTS = 60;
const CHAT_STATUS_POLL_INTERVAL_MS = 5000;

// API returns some array fields as JSON strings — parse safely
function parseArrayField<T>(value: unknown): T[] {
  if (Array.isArray(value)) return value as T[];
  if (typeof value === 'string') {
    try { const parsed = JSON.parse(value); return Array.isArray(parsed) ? parsed : []; } catch { return []; }
  }
  return [];
}

const mapDocumentDTOtoBO = (dto: DocumentDTO): ApiDocumentBO => ({
  documentId: dto.document_id,
  fileName: dto.file_name,
  fileType: dto.file_type,
  documentCategory: dto.document_category,
  pageCount: dto.page_count,
  processingStatus: dto.processing_status,
  presignedUrl: dto.presigned_url,
  downloadUrl: dto.download_url,
  uploadedAt: dto.uploaded_at,
  createdBy: dto.created_by,
  createdAt: dto.created_at,
  updatedBy: dto.updated_by,
  updatedAt: dto.updated_at,
});

const mapSessionDTOtoBO = (dto: SessionSummaryDTO): SessionSummaryBO => ({
  sessionId: dto.session_id,
  sessionTitle: dto.session_title,
  agentType: dto.agent_type,
  messageCount: dto.message_count,
  createdBy: dto.created_by,
  createdAt: dto.created_at,
  updatedBy: dto.updated_by,
  updatedAt: dto.updated_at,
});

export function useChatScreenVM() {
  const navigate = useNavigate();
  const scrollRef = useRef<HTMLDivElement>(null);
  const docPollTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Chat store
  const messages = useChatStore((s) => s.messages);
  const isStreaming = useChatStore((s) => s.isStreaming);
  const streamingMessageId = useChatStore((s) => s.streamingMessageId);
  const addUserMessage = useChatStore((s) => s.addUserMessage);
  const startStreaming = useChatStore((s) => s.startStreaming);
  const setStreamingStatus = useChatStore((s) => s.setStreamingStatus);
  const resetStreamContent = useChatStore((s) => s.resetStreamContent);
  const appendStreamToken = useChatStore((s) => s.appendStreamToken);
  const completeStream = useChatStore((s) => s.completeStream);
  const clearMessages = useChatStore((s) => s.clearMessages);
  const setMessages = useChatStore((s) => s.setMessages);
  const savedConversations = useChatStore((s) => s.savedConversations);
  const setSavedConversations = useChatStore((s) => s.setSavedConversations);
  const addSavedConversation = useChatStore((s) => s.addSavedConversation);

  // Persona store
  const activePersona = usePersonaStore((s) => s.activePersona);
  const companySetup = usePersonaStore((s) => s.companySetup);
  const activeSimulation = usePersonaStore((s) => s.activeSimulation);
  const activeScenario = usePersonaStore((s) => s.activeScenario);
  const signOut = usePersonaStore((s) => s.signOut);
  const backToLanding = usePersonaStore((s) => s.backToLanding);
  const loadChat = usePersonaStore((s) => s.loadChat);
  const setSimulation = usePersonaStore((s) => s.setSimulation);
  const setScenario = usePersonaStore((s) => s.setScenario);

  // UI store
  const citationPanelOpen = useUIStore((s) => s.citationPanelOpen);
  const toggleCitationPanel = useUIStore((s) => s.toggleCitationPanel);
  const documentViewer = useUIStore((s) => s.documentViewer);
  const openDocumentViewer = useUIStore((s) => s.openDocumentViewer);
  const closeDocumentViewer = useUIStore((s) => s.closeDocumentViewer);

  // Local state
  const [apiDocuments, setApiDocuments] = useState<ApiDocumentBO[]>([]);
  const [sessions, setSessions] = useState<SessionSummaryBO[]>([]);
  const [filterCategory, setFilterCategory] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [inputValue, setInputValue] = useState('');
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [agentType, setAgentType] = useState<string>(AgentTypeENUM.DEAL);
  const [chatLoading, setChatLoading] = useState(false);
  const [documentsLoading, setDocumentsLoading] = useState(false);
  const [chatAnalystType, setChatAnalystType] = useState<string | null>(null);

  // Derive scenario type from activeScenario or use default
  const scenarioType = activeScenario?.value ?? ScenarioTypeENUM.DEFAULT;

  // Load a session's messages via GET /chats/{chat_id}/sessions/{session_id}/messages
  const loadSessionMessages = useCallback(async (chatId: string, sessionId: string) => {
    const result = await chatListService.getSessionMessages(chatId, sessionId);
    if (result.statusCode === ServiceResultStatusENUM.OK && result.data) {
      const mapped = result.data.messages.map((m) => ({
        id: m.message_id,
        role: m.role as 'user' | 'assistant',
        content: m.content,
        timestamp: m.created_at,
        citations: m.citations?.map((c) => ({
          id: c.citation_id,
          documentId: c.document_id,
          documentName: c.document_name,
          shortName: c.short_name ?? c.document_name,
          page: c.page_number,
          section: c.section_name ?? '',
          exactQuote: c.source_text,
          label: c.label ?? `${c.document_name}, p.${c.page_number}`,
        })),
        confidence: m.confidence_level as 'high' | 'medium' | 'low' | undefined,
        assumptions: m.assumptions ? [m.assumptions] : undefined,
        calculations: (m.calculations as unknown as Record<string, unknown>[] | undefined)?.map((c) => ({
          title: c.title as string,
          steps: c.steps as string,
          result: c.result as string,
        })),
        relatedQuestions: parseArrayField<string>(m.suggested_questions),
      }));
      setMessages(mapped);
      setActiveSessionId(sessionId);
      secureStorage.setItem(SECURE_STORAGE_KEYS.ACTIVE_SESSION_ID, sessionId);
    }
  }, [setMessages]);

  // Load chat details on mount via GET /chats/{chat_id},
  // then auto-restore the last active session's messages
  useEffect(() => {
    const chatId = secureStorage.getItem(SECURE_STORAGE_KEYS.ACTIVE_CHAT_ID) as string | null;
    if (!chatId) return;

    let cancelled = false;
    const loadChatDetail = async () => {
      try {
        setChatLoading(true);
        setSessions([]);
        setSavedConversations([]);
        secureStorage.removeItem(SECURE_STORAGE_KEYS.ACTIVE_CHAT_DOCUMENTS);

        if (cancelled) return;

        const result = await chatListService.getChatDetail(chatId);
        if (cancelled) return;

        if (result.statusCode === ServiceResultStatusENUM.OK && result.data) {
          setChatAnalystType(result.data.analyst_type);
          // Update persona store with company URL from chat detail
          if (result.data.company_name) {
            loadChat(result.data.company_name, result.data.company_url || '');
          }
          const docs = result.data.documents.map(mapDocumentDTOtoBO);
          setApiDocuments(docs);
          secureStorage.setItem(SECURE_STORAGE_KEYS.ACTIVE_CHAT_DOCUMENTS, JSON.stringify(docs));

          const mappedSessions = result.data.sessions.map(mapSessionDTOtoBO);
          setSessions(mappedSessions);
          
          // Set agentType from the most recent session if available
          if (mappedSessions.length > 0) {
            const latestSession = mappedSessions[0];
            setAgentType(latestSession.agentType);
          }
          
          setSavedConversations(
            mappedSessions.map((s) => ({
              id: s.sessionId,
              title: s.sessionTitle ?? 'Untitled Session',
              timestamp: s.createdAt,
              messageCount: s.messageCount,
              preview: s.sessionTitle ?? 'Untitled Session',
            }))
          );

          // Auto-restore last active session messages on refresh
          const lastSessionId = secureStorage.getItem(SECURE_STORAGE_KEYS.ACTIVE_SESSION_ID) as string | null;
          const sessionExists = mappedSessions.some((s) => s.sessionId === lastSessionId);
          if (lastSessionId && sessionExists && !cancelled) {
            await loadSessionMessages(chatId, lastSessionId);
          }
        } else {
          const storedDocs = secureStorage.getItem(SECURE_STORAGE_KEYS.ACTIVE_CHAT_DOCUMENTS) as string | null;
          if (storedDocs) {
            try { setApiDocuments(JSON.parse(storedDocs)); } catch { /* ignore */ }
          }
        }
      } catch {
        const storedDocs = secureStorage.getItem(SECURE_STORAGE_KEYS.ACTIVE_CHAT_DOCUMENTS) as string | null;
        if (storedDocs) {
          try { setApiDocuments(JSON.parse(storedDocs)); } catch { /* ignore */ }
        }
      } finally {
        if (!cancelled) setChatLoading(false);
      }
    };

    loadChatDetail();
    return () => { cancelled = true; };
  }, []);


  // Auto-scroll on new messages
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isStreaming]);

  // Cleanup doc poll timer on unmount
  useEffect(() => {
    return () => {
      if (docPollTimerRef.current) clearTimeout(docPollTimerRef.current);
      const cancel = (docPollTimerRef as { _cancel?: () => void })._cancel;
      if (cancel) cancel();
    };
  }, []);

  // Clear chat messages on unmount so navigating back to the grid
  // never shows stale conversation state when opening a different chat
  useEffect(() => {
    return () => {
      clearMessages();
      secureStorage.removeItem(SECURE_STORAGE_KEYS.ACTIVE_SESSION_ID);
    };
  }, []);

  // Select a conversation from history: reloads documents for the chat
  // and fetches the session's messages via both GET /chats/{chat_id} and
  // GET /chats/{chat_id}/sessions/{session_id}/messages
  const handleSelectConversation = useCallback(async (sessionId: string) => {
    try {
      const chatId = secureStorage.getItem(SECURE_STORAGE_KEYS.ACTIVE_CHAT_ID) as string | null;
      if (!chatId) return;

      setChatLoading(true);

      // Run both requests in parallel
      const [detailResult, messagesResult] = await Promise.all([
        chatListService.getChatDetail(chatId),
        chatListService.getSessionMessages(chatId, sessionId),
      ]);

      // Update documents from chat detail
      if (detailResult.statusCode === ServiceResultStatusENUM.OK && detailResult.data) {
        const docs = detailResult.data.documents.map(mapDocumentDTOtoBO);
        setApiDocuments(docs);
        secureStorage.setItem(SECURE_STORAGE_KEYS.ACTIVE_CHAT_DOCUMENTS, JSON.stringify(docs));
      }

      // Update messages from session
      if (messagesResult.statusCode === ServiceResultStatusENUM.OK && messagesResult.data) {
        const mapped = messagesResult.data.messages.map((m) => ({
          id: m.message_id,
          role: m.role as 'user' | 'assistant',
          content: m.content,
          timestamp: m.created_at,
          citations: m.citations?.map((c) => ({
            id: c.citation_id,
            documentId: c.document_id,
            documentName: c.document_name,
            shortName: c.short_name ?? c.document_name,
            page: c.page_number,
            section: c.section_name ?? '',
            exactQuote: c.source_text,
            label: c.label ?? `${c.document_name}, p.${c.page_number}`,
          })),
          confidence: m.confidence_level as 'high' | 'medium' | 'low' | undefined,
          assumptions: m.assumptions ? [m.assumptions] : undefined,
          calculations: (m.calculations as unknown as Record<string, unknown>[] | undefined)?.map((c) => ({
            title: c.title as string,
            steps: c.steps as string,
            result: c.result as string,
          })),
          relatedQuestions: parseArrayField<string>(m.suggested_questions),
        }));
        setMessages(mapped);
        setActiveSessionId(sessionId);
        secureStorage.setItem(SECURE_STORAGE_KEYS.ACTIVE_SESSION_ID, sessionId);
      } else {
        toast.error(messagesResult.message || 'Failed to load conversation messages');
      }
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'An unexpected error occurred');
    } finally {
      setChatLoading(false);
    }
  }, [setMessages]);
  // Then fetches the rich response from GET /deal_conversation/{conversation_id}
  const pollForResponse = useCallback(async (conversationId: string): Promise<ConversationPollResponseDTO | null> => {
    for (let attempt = 0; attempt < MAX_POLL_ATTEMPTS; attempt++) {
      const pollResult = await chatListService.pollConversation(conversationId);
      if (pollResult.statusCode === ServiceResultStatusENUM.OK && pollResult.data) {
        if (pollResult.data.status === 'completed' || pollResult.data.status === 'failed') {
          // Fetch the rich deal conversation response
          try {
            const richResult = await apiClient.get(`/deal_conversation/${conversationId}`);
            if (richResult.data) return richResult.data as ConversationPollResponseDTO;
          } catch {
            // fallback to basic poll response
          }
          return pollResult.data;
        }
        await new Promise((resolve) => setTimeout(resolve, POLL_INTERVAL_MS));
      } else {
        return null;
      }
    }
    return null;
  }, []);


  // Send message via POST /chats/{chat_id}/stream (SSE streaming flow)
  const sendQuestion = async (question: string) => {
    if (!question.trim() || isStreaming) return;
    setInputValue('');
    addUserMessage(question);
    const msgId = `assistant-${Date.now()}`;
    startStreaming(msgId);

    try {
      const chatId = secureStorage.getItem(SECURE_STORAGE_KEYS.ACTIVE_CHAT_ID) as string | null;
      const analystType = chatAnalystType ?? PERSONA_TO_ANALYST_TYPE[activePersona.id];

      if (!chatId) {
        appendStreamToken('Unable to send message — no active chat found.');
        completeStream({
          citations: [], calculations: [], sourceExcerpts: [],
          confidence: 'low', confidenceReason: 'Missing context',
          assumptions: [], relatedQuestions: [],
        });
        return;
      }

      const isNewSession = !activeSessionId;
      let hasReceivedFirstDelta = false;

      streamMessage(
        {
          chatId,
          content: question,
          analyst_type: analystType,
          scenario_type: scenarioType,
          session_id: activeSessionId ?? undefined,
          session_title: isNewSession ? question.slice(0, 50) : undefined,
        },
        {
          onSessionInfo: (data) => {
            if (isNewSession && data.session_id) {
              setActiveSessionId(data.session_id);
              secureStorage.setItem(SECURE_STORAGE_KEYS.ACTIVE_SESSION_ID, data.session_id);
              const newSessionTitle = question.slice(0, 50);
              const newSession: SessionSummaryBO = {
                sessionId: data.session_id,
                sessionTitle: newSessionTitle,
                agentType: agentType as 'deal' | 'rfq',
                messageCount: 2,
                createdBy: 'user',
                createdAt: new Date().toISOString(),
                updatedBy: 'user',
                updatedAt: new Date().toISOString(),
              };
              setSessions((prev) => [newSession, ...prev]);
              addSavedConversation({
                id: data.session_id,
                title: newSessionTitle,
                timestamp: new Date().toISOString(),
                messageCount: 2,
                preview: question,
              });
            }
          },
          onStatus: (statusMsg) => {
            // Replace previous status with new one (reset then append)
            resetStreamContent();
            appendStreamToken(`*${statusMsg}*\n`);
          },
          onDelta: (token) => {
            if (!hasReceivedFirstDelta) {
              hasReceivedFirstDelta = true;
              resetStreamContent();
            }
            appendStreamToken(token);
          },
          onDone: (metadata) => {
            const cleanContent = (metadata.content ?? '') as string;
            const citations = (metadata.citations ?? []) as Array<Record<string, unknown>>;
            const calculations = (metadata.calculations ?? []) as Array<Record<string, unknown>>;
            const sourceExcerpts = (metadata.source_excerpts ?? []) as Array<Record<string, unknown>>;
            const confidenceLevel = (metadata.confidence_level ?? 'medium') as 'high' | 'medium' | 'low';
            const confidenceReason = (metadata.confidence_reason ?? '') as string;
            const assumptions = (metadata.assumptions ?? []) as string[];
            const suggestedQuestions = (metadata.suggested_questions ?? []) as string[];

            completeStream({
              content: cleanContent,
              citations: citations.map((c) => ({
                id: c.citation_id as string,
                documentId: c.document_id as string,
                documentName: c.document_name as string,
                shortName: (c.short_name ?? c.document_name) as string,
                page: c.page_number as number,
                section: (c.section_name ?? '') as string,
                exactQuote: c.source_text as string,
                label: (c.label ?? `${c.document_name}, p.${c.page_number}`) as string,
              })),
              calculations: calculations.map((c) => ({
                title: c.title as string,
                steps: c.steps as string,
                result: c.result as string,
              })),
              sourceExcerpts: sourceExcerpts.map((e) => ({
                citationId: e.citation_id as string,
                text: e.text as string,
                context: e.context as string,
              })),
              confidence: confidenceLevel,
              confidenceReason,
              assumptions,
              relatedQuestions: suggestedQuestions,
            });
          },
          onError: (errorMsg) => {
            appendStreamToken(errorMsg || 'An error occurred while streaming the response.');
            completeStream({
              citations: [], calculations: [], sourceExcerpts: [],
              confidence: 'low', confidenceReason: 'Streaming error',
              assumptions: [], relatedQuestions: [],
            });
          },
        },
      );
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'An unexpected error occurred';
      appendStreamToken(message);
      completeStream({
        citations: [], calculations: [], sourceExcerpts: [],
        confidence: 'low', confidenceReason: 'Exception',
        assumptions: [], relatedQuestions: [],
      });
    }
  };


  // New conversation: clears chat, resets session so next send creates a new one
  const handleNewConversation = () => {
    clearMessages();
    setActiveSessionId(null);
    secureStorage.removeItem(SECURE_STORAGE_KEYS.ACTIVE_SESSION_ID);
    toast.success('Started new conversation');
  };

  const handleSetSimulation = (simulationId: string | null) => {
    // Clear messages and reset session like new conversation
    clearMessages();
    setActiveSessionId(null);
    secureStorage.removeItem(SECURE_STORAGE_KEYS.ACTIVE_SESSION_ID);
    // Update simulation in store
    setSimulation(simulationId);
    toast.success(simulationId ? 'Simulation updated' : 'Simulation cleared');
  };

  const handleSetScenario = (scenarioId: string | null) => {
    // Clear messages and reset session like new conversation
    clearMessages();
    setActiveSessionId(null);
    secureStorage.removeItem(SECURE_STORAGE_KEYS.ACTIVE_SESSION_ID);
    // Update scenario in store
    setScenario(scenarioId);
    toast.success(scenarioId ? 'Scenario updated' : 'Scenario cleared');
  };

  const handleSignOut = () => {
    secureStorage.removeItem(SECURE_STORAGE_KEYS.ROLE);
    secureStorage.removeItem(SECURE_STORAGE_KEYS.ACTIVE_CHAT_ID);
    secureStorage.removeItem(SECURE_STORAGE_KEYS.ACTIVE_CHAT_DOCUMENTS);
    secureStorage.removeItem(SECURE_STORAGE_KEYS.ACTIVE_SESSION_ID);
    signOut();
    navigate('/role-select');
  };

  const handleBackToLanding = () => {
    clearMessages();
    secureStorage.removeItem(SECURE_STORAGE_KEYS.ACTIVE_CHAT_ID);
    secureStorage.removeItem(SECURE_STORAGE_KEYS.ACTIVE_CHAT_DOCUMENTS);
    secureStorage.removeItem(SECURE_STORAGE_KEYS.ACTIVE_SESSION_ID);
    backToLanding();
    navigate('/landing');
  };

  const handleRemoveDocument = async (documentId: string) => {
    try {
      const chatId = secureStorage.getItem(SECURE_STORAGE_KEYS.ACTIVE_CHAT_ID) as string | null;
      if (!chatId) { toast.error('No active chat found'); return; }

      const result = await chatListService.deleteDocument(chatId, documentId);
      if (result.statusCode === ServiceResultStatusENUM.OK && result.data) {
        setApiDocuments((prev) => {
          const updated = prev.filter((d) => d.documentId !== documentId);
          secureStorage.setItem(SECURE_STORAGE_KEYS.ACTIVE_CHAT_DOCUMENTS, JSON.stringify(updated));
          return updated;
        });
        toast.success(result.data.message || 'Document deleted');
      } else {
        toast.error(result.message || 'Failed to delete document');
      }
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'An unexpected error occurred');
    }
  };

  const handleUploadFile = async (file: File) => {
    try {
      const chatId = secureStorage.getItem(SECURE_STORAGE_KEYS.ACTIVE_CHAT_ID) as string | null;
      if (!chatId) { toast.error('No active chat found'); return; }

      toast.info(`Uploading ${file.name}...`);
      const result = await chatListService.uploadDocuments({ chatId, files: [file] });

      if ((result.statusCode === ServiceResultStatusENUM.CREATED || result.statusCode === ServiceResultStatusENUM.OK) && result.data) {
        const newDocs = result.data.documents.map(mapDocumentDTOtoBO);
        setApiDocuments((prev) => {
          const existingIds = new Set(prev.map((d) => d.documentId));
          const added = newDocs.filter((d) => !existingIds.has(d.documentId));
          const updated = [...prev, ...added];
          secureStorage.setItem(SECURE_STORAGE_KEYS.ACTIVE_CHAT_DOCUMENTS, JSON.stringify(updated));
          return updated;
        });
        toast.success(`${file.name} uploaded successfully`);

        // Start polling chat status until completed, then refresh documents
        setDocumentsLoading(true);
        let cancelled = false;

        const pollChatStatus = async () => {
          try {
            const statusResult = await chatListService.getChatStatus(chatId);
            if (cancelled) return;

            if (statusResult.statusCode === ServiceResultStatusENUM.OK && statusResult.data) {
              const { chat_status } = statusResult.data;
              if (chat_status === 'completed' || chat_status === 'failed') {
                // Refresh documents via GET /chats/{chat_id}
                const detailResult = await chatListService.getChatDetail(chatId);
                if (!cancelled && detailResult.statusCode === ServiceResultStatusENUM.OK && detailResult.data) {
                  const refreshedDocs = detailResult.data.documents.map(mapDocumentDTOtoBO);
                  setApiDocuments(refreshedDocs);
                  secureStorage.setItem(SECURE_STORAGE_KEYS.ACTIVE_CHAT_DOCUMENTS, JSON.stringify(refreshedDocs));
                }
                setDocumentsLoading(false);
              } else {
                docPollTimerRef.current = setTimeout(pollChatStatus, CHAT_STATUS_POLL_INTERVAL_MS);
              }
            } else {
              docPollTimerRef.current = setTimeout(pollChatStatus, CHAT_STATUS_POLL_INTERVAL_MS);
            }
          } catch {
            if (!cancelled) {
              docPollTimerRef.current = setTimeout(pollChatStatus, CHAT_STATUS_POLL_INTERVAL_MS);
            }
          }
        };

        docPollTimerRef.current = setTimeout(pollChatStatus, CHAT_STATUS_POLL_INTERVAL_MS);

        // Cleanup on unmount — attach to existing cleanup via a one-time effect
        // We store the cancel flag on the ref so the unmount effect can cancel it
        (docPollTimerRef as { _cancel?: () => void })._cancel = () => { cancelled = true; };
      } else {
        toast.error(result.message || 'Failed to upload document');
      }
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'An unexpected error occurred');
    }
  };

  // Open the citation document side panel — resolves document name from apiDocuments
  const handleOpenDocumentFromCitation = useCallback((opts: { documentId: string; page: number; highlightText?: string; citationId?: string; section?: string; documentName?: string; documentUrl?: string }) => {
    const doc = apiDocuments.find((d) => d.documentId === opts.documentId);
    openDocumentViewer({
      ...opts,
      documentName: opts.documentName || doc?.fileName,
      documentUrl: opts.documentUrl || doc?.presignedUrl,
    });
  }, [apiDocuments, openDocumentViewer]);

  const handlePreviewDocument = useCallback((documentId: string, fileName: string) => {
    openDocumentViewer({
      documentId,
      page: 1,
      documentName: fileName,
    });
  }, [openDocumentViewer]);

  const handleDownloadDocument = useCallback(async (documentId: string, fileName: string) => {
    try {
      const chatId = secureStorage.getItem(SECURE_STORAGE_KEYS.ACTIVE_CHAT_ID) as string | null;
      if (!chatId) { toast.error('No active chat found'); return; }
      toast.info(`Downloading ${fileName}...`);
      const blob = await chatListService.getDocumentFile(chatId, documentId, 'download');
      const blobUrl = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = blobUrl;
      link.download = fileName;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(blobUrl);
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Failed to download document');
    }
  }, []);

  return {
    scrollRef, chatLoading, documentsLoading,
    messages, isStreaming, streamingMessageId,
    savedConversations,
    inputValue, setInputValue,
    sendQuestion, handleNewConversation, handleSelectConversation,
    activePersona, companySetup, activeSimulation, activeScenario,
    setSimulation: handleSetSimulation, setScenario: handleSetScenario,
    handleSignOut, handleBackToLanding,
    activeSessionId, sessions, scenarioType, agentType, setAgentType,
    apiDocuments, filterCategory, searchQuery,
    setFilterCategory, setSearchQuery: setSearchQuery,
    handleRemoveDocument, handleUploadFile, handlePreviewDocument, handleDownloadDocument,
    citationPanelOpen, toggleCitationPanel,
    documentViewer, openDocumentViewer, closeDocumentViewer,
    handleOpenDocumentFromCitation,
  };
}
