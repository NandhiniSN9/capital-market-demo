export interface ApiDocumentBO {
  documentId: string;
  fileName: string;
  fileType: 'pdf' | 'pptx' | 'docx';
  documentCategory: 'financial_statement' | 'legal' | 'operational' | 'market' | null;
  pageCount: number | null;
  processingStatus: 'pending' | 'processing' | 'ready' | 'failed';
  presignedUrl: string;
  downloadUrl: string;
  uploadedAt: string;
  createdBy: string;
  createdAt: string;
  updatedBy: string;
  updatedAt: string;
}
