import { createContext, useContext } from 'react';
import { DocumentBO as Document } from '@/types/document/DocumentBO.ts';

interface DocumentState {
  documents: Document[];
  filterType: string | null;
  searchQuery: string;
}

type DocumentAction =
  | { type: 'ADD_DOCUMENT'; doc: Document }
  | { type: 'REMOVE_DOCUMENT'; id: string }
  | { type: 'UPDATE_DOCUMENT_STATUS'; id: string; status: 'ready' | 'processing' }
  | { type: 'SET_FILTER'; filterType: string | null }
  | { type: 'SET_SEARCH'; query: string }
  | { type: 'SET_COMPANY_CONTEXT'; companyName: string; baseDocs?: Document[] }
  | { type: 'RESET_DOCUMENTS' };

const documentInitialState: DocumentState = {
  documents: [],
  filterType: null,
  searchQuery: '',
};

function documentReducer(state: DocumentState, action: DocumentAction): DocumentState {
  switch (action.type) {
    case 'ADD_DOCUMENT':
      return { ...state, documents: [...state.documents, action.doc] };
    case 'REMOVE_DOCUMENT':
      return { ...state, documents: state.documents.filter((d) => d.id !== action.id) };
    case 'UPDATE_DOCUMENT_STATUS':
      return { ...state, documents: state.documents.map((d) => d.id === action.id ? { ...d, status: action.status } : d) };
    case 'SET_FILTER':
      return { ...state, filterType: action.filterType };
    case 'SET_SEARCH':
      return { ...state, searchQuery: action.query };
    case 'SET_COMPANY_CONTEXT':
      return { ...state, documents: action.baseDocs ?? [] };
    case 'RESET_DOCUMENTS':
      return { ...state, documents: [] };
    default:
      return state;
  }
}

function getFilteredDocuments(state: DocumentState): Document[] {
  let filtered = state.documents;
  if (state.filterType) filtered = filtered.filter((d) => d.type === state.filterType);
  if (state.searchQuery) {
    const q = state.searchQuery.toLowerCase();
    filtered = filtered.filter(
      (d) => d.name.toLowerCase().includes(q) || d.subType.toLowerCase().includes(q) || d.company.toLowerCase().includes(q)
    );
  }
  return filtered;
}

interface DocumentContextValue extends DocumentState {
  addDocument: (doc: Document) => void;
  removeDocument: (id: string) => void;
  updateDocumentStatus: (id: string, status: 'ready' | 'processing') => void;
  setFilter: (type: string | null) => void;
  setSearch: (query: string) => void;
  getFilteredDocuments: () => Document[];
  setCompanyContext: (companyName: string, baseDocs?: Document[]) => void;
  resetDocuments: () => void;
}

export const DocumentContext = createContext<DocumentContextValue | null>(null);

export function useDocumentStore<T>(selector: (state: DocumentContextValue) => T): T {
  const ctx = useContext(DocumentContext);
  if (!ctx) throw new Error('useDocumentStore must be used within AppProviders');
  return selector(ctx);
}

export function createDocumentContextValue(
  state: DocumentState,
  dispatch: React.Dispatch<DocumentAction>
): DocumentContextValue {
  return {
    ...state,
    addDocument: (doc) => dispatch({ type: 'ADD_DOCUMENT', doc }),
    removeDocument: (id) => dispatch({ type: 'REMOVE_DOCUMENT', id }),
    updateDocumentStatus: (id, status) => dispatch({ type: 'UPDATE_DOCUMENT_STATUS', id, status }),
    setFilter: (filterType) => dispatch({ type: 'SET_FILTER', filterType }),
    setSearch: (query) => dispatch({ type: 'SET_SEARCH', query }),
    getFilteredDocuments: () => getFilteredDocuments(state),
    setCompanyContext: (companyName, baseDocs) => dispatch({ type: 'SET_COMPANY_CONTEXT', companyName, baseDocs }),
    resetDocuments: () => dispatch({ type: 'RESET_DOCUMENTS' }),
  };
}

export { documentReducer, documentInitialState };
export type { DocumentState, DocumentAction, DocumentContextValue };
