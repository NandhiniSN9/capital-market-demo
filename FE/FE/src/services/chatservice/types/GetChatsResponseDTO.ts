export interface ChatSummaryDTO {
  chat_id: string;
  company_name: string;
  company_sector: string | null;
  analyst_type: string;
  status: string;
  document_count: number;
  session_count: number;
  created_by?: string;
  created_at?: string;
  updated_by?: string;
  updated_at?: string;
}

export interface GetChatsResponseDTO {
  chats: ChatSummaryDTO[];
  total: number;
  page: number;
  limit: number;
}
