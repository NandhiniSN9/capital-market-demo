export interface SessionSummaryBO {
  sessionId: string;
  sessionTitle: string | null;
  agentType: 'deal' | 'rfq';
  messageCount: number;
  createdBy: string;
  createdAt: string;
  updatedBy: string;
  updatedAt: string;
}
