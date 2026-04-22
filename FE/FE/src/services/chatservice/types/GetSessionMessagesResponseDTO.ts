import { CitationDTO } from './AgentResponseDTO.ts';

export interface MessageDTO {
  message_id: string;
  role: 'user' | 'assistant';
  content: string;
  citations: CitationDTO[] | null;
  confidence_level: 'high' | 'medium' | 'low' | null;
  assumptions: string | null;
  calculations: Record<string, unknown> | null;
  suggested_questions: string[] | null;
  created_by: string;
  created_at: string;
}

export interface GetSessionMessagesResponseDTO {
  messages: MessageDTO[];
}
