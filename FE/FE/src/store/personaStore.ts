import { createContext, useContext, useReducer, useMemo } from 'react';
import { PersonaBO as Persona, CompanyAnalysisBO as CompanyAnalysis, SimulationBO as Simulation } from '@/types/persona/PersonaBO.ts';
import { personas } from '@/helpers/data/personas';
import { getScenarioById, type ScenarioDefinition } from '@/helpers/data/scenarioConfig.ts';

export type AppPhase = 'role-select' | 'landing' | 'setup' | 'processing' | 'ready';

export interface CompanySetup {
  name: string;
  url: string;
}

interface PersonaState {
  activePersona: Persona;
  personas: Persona[];
  appPhase: AppPhase;
  companySetup: CompanySetup | null;
  pastAnalyses: CompanyAnalysis[];
  activeSimulation: Simulation | null;
  activeScenario: ScenarioDefinition | null;
}

type PersonaAction =
  | { type: 'SELECT_ROLE'; personaId: string }
  | { type: 'SUBMIT_SETUP'; company: CompanySetup }
  | { type: 'SET_APP_PHASE'; phase: AppPhase }
  | { type: 'SIGN_OUT' }
  | { type: 'START_NEW_ANALYSIS' }
  | { type: 'LOAD_PAST_ANALYSIS'; analysisId: string }
  | { type: 'BACK_TO_LANDING' }
  | { type: 'LOAD_CHAT'; companyName: string; companyUrl: string }
  | { type: 'SET_SIMULATION'; simulationId: string | null }
  | { type: 'SET_SCENARIO'; scenarioId: string | null };

const initialState: PersonaState = {
  activePersona: personas[0],
  personas,
  appPhase: 'role-select',
  companySetup: null,
  pastAnalyses: [],
  activeSimulation: null,
  activeScenario: null,
};

function personaReducer(state: PersonaState, action: PersonaAction): PersonaState {
  switch (action.type) {
    case 'SELECT_ROLE': {
      const persona = state.personas.find((p) => p.id === action.personaId);
      if (!persona) return state;
      return { ...state, activePersona: persona, appPhase: 'landing', companySetup: null, activeScenario: null };
    }
    case 'SUBMIT_SETUP':
      return { ...state, companySetup: action.company, appPhase: 'processing' };
    case 'SET_APP_PHASE': {
      if (action.phase === 'ready' && state.companySetup) {
        const newAnalysis: CompanyAnalysis = {
          id: `analysis-${Date.now()}`,
          companyName: state.companySetup.name,
          companyUrl: state.companySetup.url,
          personaId: state.activePersona.id,
          personaName: state.activePersona.name,
          analyzedAt: new Date().toISOString(),
          documentCount: 0,
          sector: 'General',
          status: 'completed',
        };
        const filtered = state.pastAnalyses.filter((a) => a.companyName !== state.companySetup!.name);
        return { ...state, appPhase: action.phase, pastAnalyses: [newAnalysis, ...filtered].slice(0, 10) };
      }
      return { ...state, appPhase: action.phase };
    }
    case 'SIGN_OUT':
      return { ...initialState };
    case 'START_NEW_ANALYSIS':
      return { ...state, appPhase: 'setup', activeSimulation: null, activeScenario: null };
    case 'LOAD_PAST_ANALYSIS': {
      const analysis = state.pastAnalyses.find((a) => a.id === action.analysisId);
      if (!analysis) return state;
      const persona = state.personas.find((p) => p.id === analysis.personaId);
      return {
        ...state,
        activePersona: persona || state.activePersona,
        companySetup: { name: analysis.companyName, url: analysis.companyUrl },
        appPhase: 'ready',
        activeSimulation: null,
        activeScenario: null,
      };
    }
    case 'BACK_TO_LANDING':
      return { ...state, appPhase: 'landing', companySetup: null, activeSimulation: null, activeScenario: null };
    case 'LOAD_CHAT':
      return { ...state, companySetup: { name: action.companyName, url: action.companyUrl }, appPhase: 'ready' };
    case 'SET_SIMULATION':
      return { ...state, activeSimulation: action.simulationId ? state.activeSimulation : null };
    case 'SET_SCENARIO': {
      if (!action.scenarioId) return { ...state, activeScenario: null };
      const scenario = getScenarioById(state.activePersona.id, action.scenarioId);
      return { ...state, activeScenario: scenario || null };
    }
    default:
      return state;
  }
}

interface PersonaContextValue extends PersonaState {
  selectRole: (personaId: string) => void;
  submitSetup: (company: CompanySetup) => void;
  setAppPhase: (phase: AppPhase) => void;
  signOut: () => void;
  startNewAnalysis: () => void;
  loadPastAnalysis: (analysisId: string) => void;
  backToLanding: () => void;
  loadChat: (companyName: string, companyUrl: string) => void;
  setSimulation: (simulationId: string | null) => void;
  setScenario: (scenarioId: string | null) => void;
}

export const PersonaContext = createContext<PersonaContextValue | null>(null);

export function usePersonaStore<T>(selector: (state: PersonaContextValue) => T): T {
  const ctx = useContext(PersonaContext);
  if (!ctx) throw new Error('usePersonaStore must be used within AppProviders');
  return selector(ctx);
}

export function createPersonaContextValue(
  state: PersonaState,
  dispatch: React.Dispatch<PersonaAction>
): PersonaContextValue {
  return {
    ...state,
    selectRole: (personaId) => dispatch({ type: 'SELECT_ROLE', personaId }),
    submitSetup: (company) => dispatch({ type: 'SUBMIT_SETUP', company }),
    setAppPhase: (phase) => dispatch({ type: 'SET_APP_PHASE', phase }),
    signOut: () => dispatch({ type: 'SIGN_OUT' }),
    startNewAnalysis: () => dispatch({ type: 'START_NEW_ANALYSIS' }),
    loadPastAnalysis: (analysisId) => dispatch({ type: 'LOAD_PAST_ANALYSIS', analysisId }),
    backToLanding: () => dispatch({ type: 'BACK_TO_LANDING' }),
    loadChat: (companyName, companyUrl) => dispatch({ type: 'LOAD_CHAT', companyName, companyUrl }),
    setSimulation: (simulationId) => dispatch({ type: 'SET_SIMULATION', simulationId }),
    setScenario: (scenarioId) => dispatch({ type: 'SET_SCENARIO', scenarioId }),
  };
}

export { personaReducer, initialState as personaInitialState };
export type { PersonaState, PersonaAction, PersonaContextValue };
