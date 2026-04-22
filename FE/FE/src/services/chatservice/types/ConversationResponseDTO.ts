export interface ConversationResponseDTO {
  conversation_id: string;
  session_id: string;
  status: 'in_progress' | 'completed' | 'failed';
  message?: string;
  created_at?: string;
}
