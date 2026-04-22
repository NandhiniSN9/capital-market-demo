import { createContext, useContext } from 'react';
import { MessageBO as Message, CitationBO as Citation, CalculationBO as Calculation, SourceExcerptBO as SourceExcerpt } from '@/types/chat/ChatBO.ts';

interface SavedConversation {
  id: string;
  title: string;
  timestamp: string;
  messageCount: number;
  preview: string;
}

interface ChatState {
  messages: Message[];
  isStreaming: boolean;
  streamingContent: string;
  streamingMessageId: string | null;
  streamingStatus: string | null;
  savedConversations: SavedConversation[];
}

type ChatAction =
  | { type: 'ADD_USER_MESSAGE'; content: string; id: string }
  | { type: 'START_STREAMING'; messageId: string }
  | { type: 'SET_STREAMING_STATUS'; status: string | null }
  | { type: 'RESET_STREAM_CONTENT' }
  | { type: 'APPEND_STREAM_TOKEN'; token: string }
  | { type: 'COMPLETE_STREAM'; metadata: { content?: string; citations: Citation[]; calculations?: Calculation[]; sourceExcerpts?: SourceExcerpt[]; confidence: 'high' | 'medium' | 'low'; confidenceReason: string; assumptions: string[]; relatedQuestions: string[] } }
  | { type: 'CLEAR_MESSAGES' }
  | { type: 'SAVE_CONVERSATION' }
  | { type: 'SET_SAVED_CONVERSATIONS'; conversations: SavedConversation[] }
  | { type: 'ADD_SAVED_CONVERSATION'; conversation: SavedConversation }
  | { type: 'SET_MESSAGES'; messages: Message[] };

const chatInitialState: ChatState = {
  messages: [],
  isStreaming: false,
  streamingContent: '',
  streamingMessageId: null,
  streamingStatus: null,
  savedConversations: [],
};

function chatReducer(state: ChatState, action: ChatAction): ChatState {
  switch (action.type) {
    case 'ADD_USER_MESSAGE': {
      const message: Message = { id: action.id, role: 'user', content: action.content, timestamp: new Date().toISOString() };
      return { ...state, messages: [...state.messages, message] };
    }
    case 'START_STREAMING': {
      const assistantMessage: Message = { id: action.messageId, role: 'assistant', content: '', timestamp: new Date().toISOString() };
      return { ...state, messages: [...state.messages, assistantMessage], isStreaming: true, streamingContent: '', streamingMessageId: action.messageId, streamingStatus: null };
    }
    case 'SET_STREAMING_STATUS': {
      return { ...state, streamingStatus: action.status };
    }
    case 'RESET_STREAM_CONTENT': {
      return { ...state, streamingContent: '', streamingStatus: null, messages: state.messages.map((m) => m.id === state.streamingMessageId ? { ...m, content: '' } : m) };
    }
    case 'APPEND_STREAM_TOKEN': {
      const newContent = state.streamingContent + action.token;
      // Only clear status when actual content arrives (not empty tokens)
      const newStatus = action.token ? null : state.streamingStatus;
      return { ...state, streamingContent: newContent, streamingStatus: newStatus, messages: state.messages.map((m) => m.id === state.streamingMessageId ? { ...m, content: newContent } : m) };
    }
    case 'COMPLETE_STREAM': {
      return { ...state, messages: state.messages.map((m) => m.id === state.streamingMessageId ? { ...m, ...action.metadata } : m), isStreaming: false, streamingContent: '', streamingMessageId: null, streamingStatus: null };
    }
    case 'CLEAR_MESSAGES': {
      if (state.messages.length >= 2) {
        const firstUserMsg = state.messages.find((m) => m.role === 'user');
        const saved: SavedConversation = { id: `conv-${Date.now()}`, title: firstUserMsg?.content.slice(0, 50) || 'Untitled Conversation', timestamp: new Date().toISOString(), messageCount: state.messages.length, preview: firstUserMsg?.content || '' };
        return { ...state, savedConversations: [saved, ...state.savedConversations].slice(0, 10), messages: [], isStreaming: false, streamingContent: '', streamingMessageId: null, streamingStatus: null };
      }
      return { ...state, messages: [], isStreaming: false, streamingContent: '', streamingMessageId: null, streamingStatus: null };
    }
    case 'SAVE_CONVERSATION': {
      if (state.messages.length < 2) return state;
      const firstUserMsg = state.messages.find((m) => m.role === 'user');
      const saved: SavedConversation = { id: `conv-${Date.now()}`, title: firstUserMsg?.content.slice(0, 50) || 'Untitled Conversation', timestamp: new Date().toISOString(), messageCount: state.messages.length, preview: firstUserMsg?.content || '' };
      return { ...state, savedConversations: [saved, ...state.savedConversations].slice(0, 10) };
    }
    case 'SET_SAVED_CONVERSATIONS':
      return { ...state, savedConversations: action.conversations };
    case 'ADD_SAVED_CONVERSATION':
      return { ...state, savedConversations: [action.conversation, ...state.savedConversations.filter((c) => c.id !== action.conversation.id)].slice(0, 20) };
    case 'SET_MESSAGES':
      return { ...state, messages: action.messages, isStreaming: false, streamingContent: '', streamingMessageId: null, streamingStatus: null };
    default:
      return state;
  }
}

interface ChatContextValue extends ChatState {
  addUserMessage: (content: string) => string;
  startStreaming: (messageId: string) => void;
  setStreamingStatus: (status: string | null) => void;
  resetStreamContent: () => void;
  appendStreamToken: (token: string) => void;
  completeStream: (metadata: { content?: string; citations: Citation[]; calculations?: Calculation[]; sourceExcerpts?: SourceExcerpt[]; confidence: 'high' | 'medium' | 'low'; confidenceReason: string; assumptions: string[]; relatedQuestions: string[] }) => void;
  clearMessages: () => void;
  saveCurrentConversation: () => void;
  setSavedConversations: (conversations: SavedConversation[]) => void;
  addSavedConversation: (conversation: SavedConversation) => void;
  setMessages: (messages: Message[]) => void;
}

export const ChatContext = createContext<ChatContextValue | null>(null);

export function useChatStore<T>(selector: (state: ChatContextValue) => T): T {
  const ctx = useContext(ChatContext);
  if (!ctx) throw new Error('useChatStore must be used within AppProviders');
  return selector(ctx);
}

export function createChatContextValue(
  state: ChatState,
  dispatch: React.Dispatch<ChatAction>
): ChatContextValue {
  return {
    ...state,
    addUserMessage: (content) => {
      const id = `msg-${Date.now()}`;
      dispatch({ type: 'ADD_USER_MESSAGE', content, id });
      return id;
    },
    startStreaming: (messageId) => dispatch({ type: 'START_STREAMING', messageId }),
    setStreamingStatus: (status) => dispatch({ type: 'SET_STREAMING_STATUS', status }),
    resetStreamContent: () => dispatch({ type: 'RESET_STREAM_CONTENT' }),
    appendStreamToken: (token) => dispatch({ type: 'APPEND_STREAM_TOKEN', token }),
    completeStream: (metadata) => dispatch({ type: 'COMPLETE_STREAM', metadata }),
    clearMessages: () => dispatch({ type: 'CLEAR_MESSAGES' }),
    saveCurrentConversation: () => dispatch({ type: 'SAVE_CONVERSATION' }),
    setSavedConversations: (conversations) => dispatch({ type: 'SET_SAVED_CONVERSATIONS', conversations }),
    addSavedConversation: (conversation) => dispatch({ type: 'ADD_SAVED_CONVERSATION', conversation }),
    setMessages: (messages) => dispatch({ type: 'SET_MESSAGES', messages }),
  };
}

export { chatReducer, chatInitialState };
export type { ChatState, ChatAction, ChatContextValue };
