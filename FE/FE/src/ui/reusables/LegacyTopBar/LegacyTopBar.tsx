import { useState, useRef, useEffect } from 'react';
import { BookOpen, RotateCcw, Building2, ExternalLink, LogOut, ChevronDown, ArrowLeft } from 'lucide-react';
import { ExportMenu } from '../ExportMenu/ExportMenu';
import { useUIStore } from '@/store/uiStore';
import { useChatStore } from '@/store/chatStore';
import { usePersonaStore } from '@/store/personaStore';
import { getPersonaConfig, ACCENT_CLASSES } from '@/helpers/data/personaConfig';
import { cn } from '@/helpers/utilities/utils';
import { toast } from 'sonner';
import { getPersonaProfile } from '@/helpers/data/personaProfiles';

const DATABRICKS_SYMBOL = 'https://cdn.brandfetch.io/idSUrLOWbH/theme/dark/symbol.svg?c=1bxid64Mup7aczewSAYMX&t=1668081624532';

export function TopBar() {
  const [profileOpen, setProfileOpen] = useState(false);
  const profileRef = useRef<HTMLDivElement>(null);

  const citationPanelOpen = useUIStore((s) => s.citationPanelOpen);
  const toggleCitationPanel = useUIStore((s) => s.toggleCitationPanel);
  const clearMessages = useChatStore((s) => s.clearMessages);

  const activePersona = usePersonaStore((s) => s.activePersona);
  const appPhase = usePersonaStore((s) => s.appPhase);
  const companySetup = usePersonaStore((s) => s.companySetup);
  const signOut = usePersonaStore((s) => s.signOut);
  const backToLanding = usePersonaStore((s) => s.backToLanding);

  const config = getPersonaConfig(activePersona.id);
  const accent = ACCENT_CLASSES[config.accentColor];
  const profile = getPersonaProfile(activePersona.id);

  const showCompanyContext = appPhase === 'ready' && companySetup !== null;

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (profileRef.current && !profileRef.current.contains(e.target as Node)) {
        setProfileOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  const handleNewConversation = () => {
    clearMessages();
    toast.success('Started new conversation');
  };

  return (
    <header className="flex h-14 items-center justify-between border-b border-slate-800 bg-slate-950 px-4">
      {/* Left — Databricks symbol + Deal Intelligence branding */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2.5">
          <img src={DATABRICKS_SYMBOL} alt="Databricks" className="h-7 w-7 object-contain" />
          <div>
            <h1 className="text-sm font-semibold text-slate-100 leading-tight">Deal Intelligence</h1>
            <p className="text-[10px] text-slate-500 leading-tight">AI Research Agent</p>
          </div>
        </div>

        {/* Company context chip — shown after processing */}
        {showCompanyContext && (
          <>
            <div className="mx-2 h-6 w-px bg-slate-800" />
            <div className={`flex items-center gap-2.5 rounded-lg border ${accent.chipBorder} ${accent.chipBg} px-3.5 py-1.5`}>
              <Building2 className="h-4 w-4 flex-shrink-0 text-[#2BB5D4] stroke-[1.5]" />
              <div className="flex flex-col leading-none gap-0.5">
                <span className="text-[11px] font-semibold text-[#8DD8EA]">
                  {companySetup!.name}
                </span>
                <span className="text-[9px] text-[#2BB5D4]/70 uppercase tracking-wider">
                  {config.title}
                </span>
              </div>
              <a
                href={companySetup!.url}
                target="_blank"
                rel="noopener noreferrer"
                className="ml-1.5 text-[#2BB5D4] hover:text-[#8DD8EA] transition-colors"
                title="Open investor relations page"
              >
                <ExternalLink className="h-3 w-3 stroke-[1.5]" />
              </a>
            </div>
          </>
        )}
      </div>

      {/* Right — actions + profile dropdown */}
      <div className="flex items-center gap-1">
        {appPhase === 'ready' && (
          <>
            <button
              onClick={handleNewConversation}
              className="flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs text-slate-400 hover:bg-slate-800 hover:text-slate-200 transition-colors"
            >
              <RotateCcw className="h-3.5 w-3.5 stroke-[1.5]" />
              New Chat
            </button>
            <button
              onClick={toggleCitationPanel}
              className={cn(
                'flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs transition-colors',
                citationPanelOpen
                  ? 'bg-[#145D70]/15 text-[#2BB5D4]'
                  : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
              )}
            >
              <BookOpen className="h-3.5 w-3.5 stroke-[1.5]" />
              Sources
            </button>
            <ExportMenu />

            {/* Separator */}
            <div className="mx-1.5 h-6 w-px bg-slate-800" />
          </>
        )}

        {/* Profile dropdown */}
        <div className="relative" ref={profileRef}>
          <button
            onClick={() => setProfileOpen(!profileOpen)}
            className="flex items-center gap-2.5 rounded-md px-2 py-1.5 transition-colors hover:bg-slate-800"
          >
            {/* Avatar */}
            <img
              src={profile.photo}
              alt={profile.name}
              className="h-7 w-7 rounded-full object-cover flex-shrink-0"
            />
            <div className="text-left">
              <p className="text-xs font-semibold text-white leading-tight">{profile.name}</p>
              <p className="text-[10px] font-medium leading-tight text-[#2BB5D4]">{activePersona.name}</p>
            </div>
            <ChevronDown className={cn('h-3 w-3 text-slate-500 transition-transform stroke-[1.5]', profileOpen && 'rotate-180')} />
          </button>

          {/* Dropdown menu */}
          {profileOpen && (
            <div className="absolute right-0 top-full mt-1 z-50 w-56 rounded-lg border border-slate-700 bg-slate-900 p-1 shadow-xl shadow-black/50">
              {/* Profile info */}
              <div className="px-3 py-2.5">
                <p className="text-xs font-semibold text-white">{profile.name}</p>
                <p className="text-[10px] text-[#2BB5D4]">{activePersona.name}</p>
              </div>
              <div className="mx-2 h-px bg-slate-700/80" />
              {/* Back to analyses — hidden on landing page */}
              {appPhase !== 'landing' && (
                <button
                  onClick={() => {
                    setProfileOpen(false);
                    backToLanding();
                  }}
                  className="flex w-full items-center gap-2 rounded-md px-3 py-2 mt-1 text-xs text-slate-400 hover:bg-slate-800 hover:text-slate-200 transition-colors"
                >
                  <ArrowLeft className="h-3.5 w-3.5 stroke-[1.5]" />
                  Back to Analyses
                </button>
              )}
              {/* Sign out */}
              <button
                onClick={() => {
                  setProfileOpen(false);
                  signOut();
                }}
                className="flex w-full items-center gap-2 rounded-md px-3 py-2 mt-1 text-xs text-slate-400 hover:bg-slate-800 hover:text-slate-200 transition-colors"
              >
                <LogOut className="h-3.5 w-3.5 stroke-[1.5]" />
                Sign Out
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
