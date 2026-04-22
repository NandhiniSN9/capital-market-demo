export interface CitationBO {
  id: string;
  documentId: string;
  documentName: string;
  shortName: string;
  page: number;
  section: string;
  exactQuote: string;
  label: string;
}

export interface CalculationBO {
  title: string;
  steps: string;
  result: string;
}

export interface SourceExcerptBO {
  citationId: string;
  text: string;
  context: string;
}

export interface MessageBO {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  citations?: CitationBO[];
  calculations?: CalculationBO[];
  sourceExcerpts?: SourceExcerptBO[];
  confidence?: 'high' | 'medium' | 'low';
  confidenceReason?: string;
  assumptions?: string[];
  relatedQuestions?: string[];
}

export interface SavedConversationBO {
  id: string;
  title: string;
  timestamp: string;
  messageCount: number;
  preview: string;
}
