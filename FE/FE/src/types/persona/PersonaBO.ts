export interface PersonaBO {
  id: string;
  name: string;
  shortName: string;
  icon: string;
  description: string;
  suggestedQuestions: string[];
}

export interface CompanySetupBO {
  name: string;
  url: string;
}

export interface CompanyAnalysisBO {
  id: string;
  companyName: string;
  companyUrl: string;
  personaId: string;
  personaName: string;
  analyzedAt: string;
  documentCount: number;
  sector: string;
  status: 'completed' | 'in-progress';
}

export interface SimulationBO {
  id: string;
  personaId: string;
  name: string;
  shortName: string;
  description: string;
  suggestedQuestions: string[];
  documentSetId: string;
  responseIds: string[];
}

export type AppPhaseENUM = 'role-select' | 'landing' | 'setup' | 'processing' | 'ready';
