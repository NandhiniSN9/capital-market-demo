export interface CitationDTO {
  citation_id: string;
  document_id: string;
  document_name: string;
  short_name?: string;
  page_number: number;
  section_name: string | null;
  source_text: string;
  label?: string;
}

export interface AgentResponseDTO {
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
