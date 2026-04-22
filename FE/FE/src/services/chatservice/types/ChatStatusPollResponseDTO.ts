export interface ChatStatusPollResponseDTO {
  status: string;
  chat_id: string;
  chat_status: 'in_progress' | 'active' | 'completed' | 'failed';
}
