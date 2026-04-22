import { Loader2 } from 'lucide-react';
import { useChatScreenVM } from './ChatScreen.vm.ts';
import { TopBar } from '../../reusables/TopBar/TopBar.tsx';
import { DocumentPanel } from '../../reusables/DocumentPanel/DocumentPanel.tsx';
import { ChatPanel } from '../../reusables/ChatPanel/ChatPanel.tsx';
import { CitationSidePanel } from '../../reusables/CitationSidePanel/CitationSidePanel.tsx';
import { CitationDocumentPanel } from '../../reusables/CitationDocumentPanel/CitationDocumentPanel.tsx';
import './ChatScreen.css';

export function ChatScreen() {
  const vm = useChatScreenVM();

  return (
    <div className="chat-screen-root">
      {vm.chatLoading && (
        <div className="chat-screen-loader" role="status" aria-label="Loading dashboard">
          <Loader2 size={32} className="animate-spin" style={{ color: '#2BB5D4' }} aria-hidden="true" />
          <p className="chat-screen-loader-text">Loading your dashboard...</p>
        </div>
      )}
      <TopBar
        companySetup={vm.companySetup}
        activePersona={vm.activePersona}
        activeSimulation={vm.activeSimulation}
        activeScenario={vm.activeScenario}
        citationPanelOpen={vm.citationPanelOpen}
        onToggleCitationPanel={vm.toggleCitationPanel}
        onNewConversation={vm.handleNewConversation}
        onSignOut={vm.handleSignOut}
        onBackToLanding={vm.handleBackToLanding}
        onSetSimulation={vm.setSimulation}
        onSetScenario={vm.setScenario}
        showActions
      />

      <div className="chat-screen-body">
        <div className="chat-screen-panels">
          {/* Left: Document library */}
          <aside className="chat-left-panel" aria-label="Document library">
            <DocumentPanel
              documents={vm.apiDocuments}
              filterCategory={vm.filterCategory}
              searchQuery={vm.searchQuery}
              onSetFilter={vm.setFilterCategory}
              onSetSearch={vm.setSearchQuery}
              onRemoveDocument={vm.handleRemoveDocument}
              onUploadFile={vm.handleUploadFile}
              onPreviewDocument={vm.handlePreviewDocument}
              onDownloadDocument={vm.handleDownloadDocument}
              savedConversations={vm.savedConversations}
              onSelectConversation={vm.handleSelectConversation}
              documentsLoading={vm.documentsLoading}
            />
          </aside>

          {/* Right: Chat */}
          <main className="chat-right-panel" aria-label="Chat interface">
            <ChatPanel
              messages={vm.messages}
              isStreaming={vm.isStreaming}
              streamingMessageId={vm.streamingMessageId}
              scrollRef={vm.scrollRef}
              activePersona={vm.activePersona}
              activeSimulation={vm.activeSimulation}
              activeScenario={vm.activeScenario}
              companySetup={vm.companySetup}
              inputValue={vm.inputValue}
              onInputChange={vm.setInputValue}
              onSendQuestion={vm.sendQuestion}
              onOpenDocument={vm.handleOpenDocumentFromCitation}
            />
          </main>

          {/* Citation side panel */}
          {vm.citationPanelOpen && (
            <CitationSidePanel
              messages={vm.messages}
              onClose={vm.toggleCitationPanel}
              onOpenDocument={vm.handleOpenDocumentFromCitation}
            />
          )}

          {/* Citation document viewer side panel */}
          {vm.documentViewer.isOpen && (
            <aside className="chat-citation-doc-panel" aria-label="Citation document viewer">
              <CitationDocumentPanel
                documentViewer={vm.documentViewer}
                documents={vm.apiDocuments}
                onClose={vm.closeDocumentViewer}
                onNavigate={vm.handleOpenDocumentFromCitation}
              />
            </aside>
          )}
        </div>
      </div>
    </div>
  );
}
