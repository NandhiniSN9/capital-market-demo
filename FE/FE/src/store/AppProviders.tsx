import { useReducer, useMemo } from 'react';
import { PersonaContext, personaReducer, personaInitialState, createPersonaContextValue } from './personaStore.ts';
import { ChatContext, chatReducer, chatInitialState, createChatContextValue } from './chatStore.ts';
import { UIContext, uiReducer, uiInitialState, createUIContextValue } from './uiStore.ts';
import { DocumentContext, documentReducer, documentInitialState, createDocumentContextValue } from './documentStore.ts';

export function AppProviders({ children }: { children: React.ReactNode }) {
  const [personaState, personaDispatch] = useReducer(personaReducer, personaInitialState);
  const [chatState, chatDispatch] = useReducer(chatReducer, chatInitialState);
  const [uiState, uiDispatch] = useReducer(uiReducer, uiInitialState);
  const [documentState, documentDispatch] = useReducer(documentReducer, documentInitialState);

  const personaValue = useMemo(() => createPersonaContextValue(personaState, personaDispatch), [personaState]);
  const chatValue = useMemo(() => createChatContextValue(chatState, chatDispatch), [chatState]);
  const uiValue = useMemo(() => createUIContextValue(uiState, uiDispatch), [uiState]);
  const documentValue = useMemo(() => createDocumentContextValue(documentState, documentDispatch), [documentState]);

  return (
    <PersonaContext.Provider value={personaValue}>
      <ChatContext.Provider value={chatValue}>
        <UIContext.Provider value={uiValue}>
          <DocumentContext.Provider value={documentValue}>
            {children}
          </DocumentContext.Provider>
        </UIContext.Provider>
      </ChatContext.Provider>
    </PersonaContext.Provider>
  );
}
