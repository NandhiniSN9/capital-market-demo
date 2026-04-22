import { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import secureStorage from 'react-secure-storage';
import { usePersonaStore } from '../../../store/personaStore.ts';
import { ChatSummaryBO } from '../../../types/chat/ChatSummaryBO.ts';
import { ServiceResultStatusENUM } from '../../../types/service/ServiceResultStatusENUM.ts';
import { chatListService } from '../../../services/chatservice/chatListServiceSelector.ts';
import { SECURE_STORAGE_KEYS } from '../../../helpers/storage/secureStorageKeys.ts';
import { PERSONA_TO_ANALYST_TYPE } from '../../../helpers/config/analystTypeMap.ts';
import { getPollingChat, clearPollingChat } from '../../../helpers/storage/pollingChatMap.ts';
import { ChatSummaryDTO } from '../../../services/chatservice/types/GetChatsResponseDTO.ts';

const CHAT_STATUS_POLL_INTERVAL_MS = 5000;

const mapChatSummaryDTOtoBO = (dto: ChatSummaryDTO): ChatSummaryBO => ({
  chatId: dto.chat_id,
  companyName: dto.company_name,
  companySector: dto.company_sector,
  analystType: dto.analyst_type,
  status: dto.status,
  documentCount: dto.document_count,
  sessionCount: dto.session_count,
  createdBy: dto.created_by,
  createdAt: dto.created_at,
  updatedBy: dto.updated_by,
  updatedAt: dto.updated_at,
});

export function useLandingVM() {
  const navigate = useNavigate();
  const activePersona = usePersonaStore((s) => s.activePersona);
  const startNewAnalysis = usePersonaStore((s) => s.startNewAnalysis);
  const submitSetup = usePersonaStore((s) => s.submitSetup);
  const setAppPhase = usePersonaStore((s) => s.setAppPhase);
  const loadChat = usePersonaStore((s) => s.loadChat);

  const [chats, setChats] = useState<ChatSummaryBO[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pollingChatId, setPollingChatId] = useState<string | null>(null);

  const pollTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  // Keep a ref in sync with chats so effects can read the latest value without being in deps
  const chatsRef = useRef<ChatSummaryBO[]>([]);

  // ─── Fetch chats list ────────────────────────────────────────────────────────
  const fetchChats = useCallback(async (cancelled: { value: boolean }, retryCount = 0) => {
    const MAX_RETRIES = 5;
    try {
      if (retryCount === 0) setLoading(true);
      setError(null);

      const analystType = PERSONA_TO_ANALYST_TYPE[activePersona.id];
      const result = await chatListService.getChats({ analyst_type: analystType });
      if (cancelled.value) return;

      if (result && result.statusCode === ServiceResultStatusENUM.OK && result.data) {
        const mapped = result.data.chats.map(mapChatSummaryDTOtoBO);
        // Sort by created_at descending (newest first)
        mapped.sort((a, b) => new Date(b.createdAt ?? 0).getTime() - new Date(a.createdAt ?? 0).getTime());
        chatsRef.current = mapped;
        setChats(mapped);
      } else {
        const msg = result?.message ?? '';
        const isTimeout = msg.toLowerCase().includes('timeout') || msg.includes('ECONNABORTED');
        if (isTimeout && retryCount < MAX_RETRIES && !cancelled.value) {
          console.warn(`[fetchChats] Timeout detected, retrying (${retryCount + 1}/${MAX_RETRIES})...`);
          return await fetchChats(cancelled, retryCount + 1);
        }
        setError(result?.message || 'Failed to load chats. Please try again.');
      }
    } catch (err: unknown) {
      if (!cancelled.value) {
        const msg = err instanceof Error ? err.message : '';
        const isTimeout = msg.toLowerCase().includes('timeout') || msg.includes('ECONNABORTED');
        if (isTimeout && retryCount < MAX_RETRIES) {
          console.warn(`[fetchChats] Timeout exception, retrying (${retryCount + 1}/${MAX_RETRIES})...`);
          return await fetchChats(cancelled, retryCount + 1);
        }
        setError(msg || 'An unexpected error occurred.');
      }
    } finally {
      if (!cancelled.value && retryCount === 0) setLoading(false);
    }
  }, [activePersona.id]); // eslint-disable-line react-hooks/exhaustive-deps

  // ─── Initial load + pick up any in-flight polling chat from storage ──────────
  useEffect(() => {
    const cancelled = { value: false };

    const loadAndMaybeStartPolling = async () => {
      const currentRole = PERSONA_TO_ANALYST_TYPE[activePersona.id];

      await fetchChats(cancelled);
      if (cancelled.value) return;

      const storedPollingId = getPollingChat(currentRole);
      if (!storedPollingId) return;

      // Use the ref to read the latest chats without triggering re-renders
      const match = chatsRef.current.find((c) => c.chatId === storedPollingId);
      
      // Clear polling if chat doesn't exist in the list OR if it's already done
      if (!match) {
        // Chat ID not found in the fetched list - clear stale polling state
        clearPollingChat(currentRole);
      } else {
        const alreadyDone =
          match.status === 'completed' || match.status === 'active' || match.status === 'failed';

        if (alreadyDone) {
          clearPollingChat(currentRole);
        } else {
          setPollingChatId(storedPollingId);
        }
      }
    };

    loadAndMaybeStartPolling();
    return () => { cancelled.value = true; };
  }, [fetchChats]); // fetchChats is stable per activePersona.id via useCallback

  // ─── Polling loop ────────────────────────────────────────────────────────────
  useEffect(() => {
    if (!pollingChatId) return;

    const roleAtPollStart = PERSONA_TO_ANALYST_TYPE[activePersona.id];
    let cancelled = false;

    const poll = async () => {
      try {
        const result = await chatListService.getChatStatus(pollingChatId);
        if (cancelled) return;

        if (result.statusCode === ServiceResultStatusENUM.OK && result.data) {
          const { chat_status } = result.data;

          if (chat_status === 'completed' || chat_status === 'active' || chat_status === 'failed') {
            setChats((prev) => {
              const updated = prev.map((c) =>
                c.chatId === pollingChatId ? { ...c, status: chat_status } : c
              );
              chatsRef.current = updated;
              return updated;
            });
            setPollingChatId(null);
            clearPollingChat(roleAtPollStart);
          } else {
            pollTimerRef.current = setTimeout(poll, CHAT_STATUS_POLL_INTERVAL_MS);
          }
        } else {
          pollTimerRef.current = setTimeout(poll, CHAT_STATUS_POLL_INTERVAL_MS);
        }
      } catch {
        if (!cancelled) {
          pollTimerRef.current = setTimeout(poll, CHAT_STATUS_POLL_INTERVAL_MS);
        }
      }
    };

    poll();

    return () => {
      cancelled = true;
      if (pollTimerRef.current) clearTimeout(pollTimerRef.current);
    };
  }, [pollingChatId]); // eslint-disable-line react-hooks/exhaustive-deps

  // ─── Actions ─────────────────────────────────────────────────────────────────
  const handleStartNew = () => {
    startNewAnalysis();
    navigate('/setup');
  };

  const handleLoadChat = (chat: ChatSummaryBO) => {
    // Prevent navigation if chat is still being processed
    if (chat.status === 'in_progress' || chat.status === 'processing') return;
    if (chat.chatId === pollingChatId) return;
    secureStorage.setItem(SECURE_STORAGE_KEYS.ACTIVE_CHAT_ID, chat.chatId);
    loadChat(chat.companyName, '');
    navigate('/ready');
  };

  const formatRelativeDate = (isoDate: string): string => {
    const diff = Date.now() - new Date(isoDate).getTime();
    const days = Math.floor(diff / 86400000);
    if (days <= 0) return 'Today';
    if (days === 1) return 'Yesterday';
    if (days < 30) return `${days} days ago`;
    return new Date(isoDate).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  };

  const pollingChat = chats.find((c) => c.chatId === pollingChatId);
  const isActivelyPolling =
    pollingChatId !== null &&
    (!pollingChat || pollingChat.status === 'in_progress' || pollingChat.status === 'processing');

  return {
    activePersona,
    chats,
    loading,
    error,
    pollingChatId,
    isActivelyPolling,
    handleStartNew,
    handleLoadChat,
    formatRelativeDate,
  };
}
 