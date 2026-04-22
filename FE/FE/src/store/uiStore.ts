import { createContext, useContext } from 'react';

interface DocumentViewerState {
  isOpen: boolean;
  documentId: string | null;
  documentName: string | null;
  documentUrl: string | null;
  page: number;
  highlightText: string | null;
  citationId: string | null;
  section: string | null;
}

interface UIState {
  leftPanelWidth: number;
  documentViewer: DocumentViewerState;
  citationPanelOpen: boolean;
}

type UIAction =
  | { type: 'SET_LEFT_PANEL_WIDTH'; width: number }
  | { type: 'OPEN_DOCUMENT_VIEWER'; opts: { documentId: string; page: number; highlightText?: string; citationId?: string; section?: string; documentName?: string; documentUrl?: string } }
  | { type: 'CLOSE_DOCUMENT_VIEWER' }
  | { type: 'TOGGLE_CITATION_PANEL' };

const uiInitialState: UIState = {
  leftPanelWidth: 35,
  documentViewer: { isOpen: false, documentId: null, documentName: null, documentUrl: null, page: 1, highlightText: null, citationId: null, section: null },
  citationPanelOpen: false,
};

function uiReducer(state: UIState, action: UIAction): UIState {
  switch (action.type) {
    case 'SET_LEFT_PANEL_WIDTH':
      return { ...state, leftPanelWidth: action.width };
    case 'OPEN_DOCUMENT_VIEWER':
      return { ...state, documentViewer: { isOpen: true, documentId: action.opts.documentId, documentName: action.opts.documentName || null, documentUrl: action.opts.documentUrl || null, page: action.opts.page, highlightText: action.opts.highlightText || null, citationId: action.opts.citationId || null, section: action.opts.section || null } };
    case 'CLOSE_DOCUMENT_VIEWER':
      return { ...state, documentViewer: { isOpen: false, documentId: null, documentName: null, documentUrl: null, page: 1, highlightText: null, citationId: null, section: null } };
    case 'TOGGLE_CITATION_PANEL':
      return { ...state, citationPanelOpen: !state.citationPanelOpen };
    default:
      return state;
  }
}

interface UIContextValue extends UIState {
  setLeftPanelWidth: (width: number) => void;
  openDocumentViewer: (opts: { documentId: string; page: number; highlightText?: string; citationId?: string; section?: string; documentName?: string; documentUrl?: string }) => void;
  closeDocumentViewer: () => void;
  toggleCitationPanel: () => void;
}

export const UIContext = createContext<UIContextValue | null>(null);

export function useUIStore<T>(selector: (state: UIContextValue) => T): T {
  const ctx = useContext(UIContext);
  if (!ctx) throw new Error('useUIStore must be used within AppProviders');
  return selector(ctx);
}

export function createUIContextValue(
  state: UIState,
  dispatch: React.Dispatch<UIAction>
): UIContextValue {
  return {
    ...state,
    setLeftPanelWidth: (width) => dispatch({ type: 'SET_LEFT_PANEL_WIDTH', width }),
    openDocumentViewer: (opts) => dispatch({ type: 'OPEN_DOCUMENT_VIEWER', opts }),
    closeDocumentViewer: () => dispatch({ type: 'CLOSE_DOCUMENT_VIEWER' }),
    toggleCitationPanel: () => dispatch({ type: 'TOGGLE_CITATION_PANEL' }),
  };
}

export { uiReducer, uiInitialState };
export type { UIState, UIAction, UIContextValue };
