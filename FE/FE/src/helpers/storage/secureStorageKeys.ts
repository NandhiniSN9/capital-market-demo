export const SECURE_STORAGE_KEYS = {
  ROLE: 'role',
  ACTIVE_CHAT_ID: 'active_chat_id',
  ACTIVE_CHAT_DOCUMENTS: 'active_chat_documents',
  ACTIVE_SESSION_ID: 'active_session_id',
  // Map of role -> chatId for in-progress polling, keyed by analyst role
  POLLING_CHAT_MAP: 'polling_chat_map',
} as const;
