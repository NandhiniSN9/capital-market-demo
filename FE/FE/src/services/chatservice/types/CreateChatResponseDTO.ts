export interface DocumentDTO {
  document_id: string;
  file_name: string;
  file_type: 'pdf' | 'pptx' | 'docx';
  document_category: 'financial_statement' | 'legal' | 'operational' | 'market' | null;
  page_count: number | null;
  processing_status: 'pending' | 'processing' | 'ready' | 'failed';
  presigned_url: string;
  download_url: string;
  uploaded_at: string;
  created_by: string;
  created_at: string;
  updated_by: string;
  updated_at: string;
}

export interface CreateChatResponseDTO {
  chat_id: string;
  company_name: string;
  company_url: string | null;
  company_sector: string | null;
  analyst_type: string;
  status: string;
  document_count: number;
  documents: DocumentDTO[];
  created_by: string;
  created_at: string;
  updated_by: string;
  updated_at: string;
}
