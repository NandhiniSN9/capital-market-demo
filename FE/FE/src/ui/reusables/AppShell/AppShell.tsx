import { Panel, Group, Separator } from 'react-resizable-panels';
import { TopBar } from '@/ui/reusables/LegacyTopBar/LegacyTopBar';
import { LeftPanel } from '@/ui/reusables/LeftPanel/LeftPanel';
import { RightPanel } from '@/ui/reusables/RightPanel/RightPanel';
import { DocumentViewer } from '@/ui/reusables/DocumentViewer/DocumentViewer';
import { CitationPanel } from '@/ui/reusables/CitationPanel/CitationPanel';
import { RoleSelectionPage } from '@/ui/reusables/RoleSelectionPage/RoleSelectionPage';
import { LandingPage } from '@/ui/reusables/LandingPage/LandingPage';
import { useUIStore } from '@/store/uiStore';
import { usePersonaStore } from '@/store/personaStore';
import { X } from 'lucide-react';

export function AppShell() {
  const documentViewer = useUIStore((s) => s.documentViewer);
  const citationPanelOpen = useUIStore((s) => s.citationPanelOpen);
  const toggleCitationPanel = useUIStore((s) => s.toggleCitationPanel);

  const appPhase = usePersonaStore((s) => s.appPhase);

  // Show role selection page as full screen
  if (appPhase === 'role-select') {
    return (
      <div className="flex h-screen flex-col overflow-hidden bg-slate-950">
        <RoleSelectionPage />
      </div>
    );
  }

  // Show landing page with TopBar (logo + profile only)
  if (appPhase === 'landing') {
    return (
      <div className="flex h-screen flex-col overflow-hidden bg-slate-950">
        <TopBar />
        <LandingPage />
      </div>
    );
  }

  // Hide the left documents panel until analysis is complete
  const showLeftPanel = appPhase === 'ready';
  const showTopBar = true; // TopBar shows on setup, processing, and ready phases

  return (
    <div className="flex h-screen flex-col overflow-hidden bg-slate-950">
      {showTopBar && <TopBar />}
      <div className="flex flex-1 overflow-hidden">
        {/* Main resizable panels */}
        <div className="flex-1 overflow-hidden">
          <Group orientation="horizontal" className="h-full">
            {showLeftPanel && (
              <>
                <Panel defaultSize="320px" minSize="240px" maxSize="480px">
                  <LeftPanel />
                </Panel>
                <Separator className="w-1 bg-slate-800 hover:bg-[#145D70]/50 transition-colors duration-150 data-[resize-handle-active]:bg-[#2BB5D4]" />
              </>
            )}
            <Panel minSize="50%">
              <RightPanel />
            </Panel>
          </Group>
        </div>

        {/* Citation/Sources Panel - part of flex layout, slides in from right */}
        {citationPanelOpen && (
          <div className="w-80 flex-shrink-0 border-l border-slate-700 bg-slate-950 shadow-2xl shadow-black/50">
            <div className="relative h-full">
              <div className="absolute top-2 right-2 z-10">
                <button
                  onClick={toggleCitationPanel}
                  className="flex h-6 w-6 items-center justify-center rounded-md text-slate-500 hover:bg-slate-800 hover:text-slate-300 transition-colors"
                >
                  <X className="h-3.5 w-3.5" />
                </button>
              </div>
              <CitationPanel />
            </div>
          </div>
        )}
      </div>

      {documentViewer.isOpen && <DocumentViewer />}
    </div>
  );
}
