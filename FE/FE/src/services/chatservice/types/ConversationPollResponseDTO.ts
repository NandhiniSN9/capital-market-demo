import { CitationDTO } from './AgentResponseDTO.ts';

export interface CalculationDTO {
  title: string;
  steps: string;
  result: string;
}

export interface SourceExcerptDTO {
  citation_id: string;
  text: string;
  context: string;
}

export interface ConversationPollResponseDTO {
  conversation_id: string;
  session_id: string;
  status: 'in_progress' | 'completed' | 'failed';
  user_query?: string;
  analyst_type?: string;
  scenario_type?: string;
  content?: string | null;
  citations?: CitationDTO[] | null;
  confidence_level?: 'high' | 'medium' | 'low' | null;
  confidence_reason?: string | null;
  calculations?: CalculationDTO[] | null;
  source_excerpts?: SourceExcerptDTO[] | null;
  assumptions?: string[] | null;
  suggested_questions?: string[] | null;
  error_message?: string | null;
  created_at?: string;
  updated_at?: string;
}
