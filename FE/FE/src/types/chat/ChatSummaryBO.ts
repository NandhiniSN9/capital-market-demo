export interface ChatSummaryBO {
  chatId: string;
  companyName: string;
  companySector: string | null;
  analystType: string;
  status: string;
  documentCount: number;
  sessionCount: number;
  createdBy?: string;
  createdAt?: string;
  updatedBy?: string;
  updatedAt?: string;
}
