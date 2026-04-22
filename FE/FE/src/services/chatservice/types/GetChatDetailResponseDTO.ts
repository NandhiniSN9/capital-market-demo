import { DocumentDTO } from './CreateChatResponseDTO.ts';

export interface SessionSummaryDTO {
  session_id: string;
  session_title: string | null;
  agent_type: 'deal' | 'rfq';
  message_count: number;
  created_by: string;
  created_at: string;
  updated_by: string;
  updated_at: string;
}

export interface GetChatDetailResponseDTO {
  chat_id: string;
  company_name: string;
  company_url: string | null;
  company_sector: string | null;
  analyst_type: string;
  status: string;
  document_count: number;
  documents: DocumentDTO[];
  sessions: SessionSummaryDTO[];
  created_by: string;
  created_at: string;
  updated_by: string;
  updated_at: string;
}
