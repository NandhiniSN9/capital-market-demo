import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { BookOpen, RotateCcw, Building2, ExternalLink, LogOut, ChevronDown, ArrowLeft, FlaskConical, Download, Copy, FileText, Save, Share2, Check } from 'lucide-react';
import { PersonaBO, CompanySetupBO, SimulationBO } from '../../../types/persona/PersonaBO.ts';
import { getPersonaConfig } from '../../../helpers/data/personaConfig.ts';
import { getPersonaProfile } from '../../../helpers/data/personaProfiles.ts';
import { getScenariosForPersona, type ScenarioDefinition } from '../../../helpers/data/scenarioConfig.ts';
import { useChatStore } from '../../../store/chatStore.ts';
import { toast } from 'sonner';
import './TopBar.css';

const DATABRICKS_SYMBOL = 'https://cdn.brandfetch.io/idSUrLOWbH/theme/dark/symbol.svg?c=1bxid64Mup7aczewSAYMX&t=1668081624532';

interface TopBarProps {
  activePersona?: PersonaBO;
  companySetup?: CompanySetupBO | null;
  activeSimulation?: SimulationBO | null;
  activeScenario?: ScenarioDefinition | null;
  citationPanelOpen?: boolean;
  showActions?: boolean;
  onToggleCitationPanel?: () => void;
  onNewConversation?: () => void;
  onSignOut?: () => void;
  onBackToLanding?: () => void;
  onSetSimulation?: (id: string | null) => void;
  onSetScenario?: (id: string | null) => void;
}

export function TopBar({
  activePersona,
  companySetup,
  activeSimulation,
  activeScenario,
  citationPanelOpen,
  showActions,
  onToggleCitationPanel,
  onNewConversation,
  onSignOut,
  onBackToLanding,
  onSetSimulation,
  onSetScenario,
}: TopBarProps) {
  const [profileOpen, setProfileOpen] = useState(false);
  const [scenarioOpen, setScenarioOpen] = useState(false);
  const [exportOpen, setExportOpen] = useState(false);
  const [copied, setCopied] = useState(false);
  const profileRef = useRef<HTMLDivElement>(null);
  const scenarioRef = useRef<HTMLDivElement>(null);
  const exportRef = useRef<HTMLDivElement>(null);

  const messages = useChatStore((s) => s.messages);
  const navigate = useNavigate();

  const profile = activePersona ? getPersonaProfile(activePersona.id) : null;
  const config = activePersona ? getPersonaConfig(activePersona.id) : null;
  const availableScenarios = activePersona ? getScenariosForPersona(activePersona.id) : [];
  const showScenarioDropdown = showActions && companySetup && availableScenarios.length > 0;

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (profileRef.current && !profileRef.current.contains(e.target as Node)) setProfileOpen(false);
      if (scenarioRef.current && !scenarioRef.current.contains(e.target as Node)) setScenarioOpen(false);
      if (exportRef.current && !exportRef.current.contains(e.target as Node)) setExportOpen(false);
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  const handleExportPDF = () => {
    if (!messages.length) { toast.error('No conversation to export'); return; }
    const content = messages.map((m) => {
      const clean = m.content.replace(/\{\{cit:[^}]+\}\}/g, '');
      return m.role === 'user'
        ? `<div style="text-align:right;padding:12px 16px;background:#1e293b;border-radius:12px;color:#e2e8f0;font-size:14px;margin:12px 0;">${clean}</div>`
        : `<div style="padding:16px;background:#0f172a;border:1px solid #334155;border-radius:12px;color:#cbd5e1;font-size:13px;line-height:1.7;margin:12px 0;">${clean.replace(/\n/g, '<br/>')}</div>`;
    }).join('');
    const html = `<!DOCTYPE html><html><head><title>Deal Intelligence Export</title><style>body{font-family:system-ui;background:#020617;padding:32px;max-width:800px;margin:0 auto;}h1{color:#38bdf8;font-size:18px;}p{color:#64748b;font-size:11px;margin-bottom:24px;}</style></head><body><h1>Deal Intelligence</h1><p>Exported ${new Date().toLocaleString()}</p>${content}</body></html>`;
    const w = window.open('', '_blank');
    if (w) { w.document.write(html); w.document.close(); setTimeout(() => w.print(), 500); }
    toast.success('PDF export opened');
  };

  return (
    <header className="topbar" role="banner">
      <div className="topbar-left">
        {/* Brand */}
        <div className="topbar-brand" onClick={() => { if (onSignOut) { onSignOut(); } navigate('/role-select'); }} style={{ cursor: 'pointer' }} role="link" aria-label="Go to home page">
          <img src={DATABRICKS_SYMBOL} alt="Databricks" style={{ height: '1.75rem', width: '1.75rem', objectFit: 'contain' }} />
          <div className="topbar-brand-text">
            <h1>Deal Intelligence</h1>
            <p>AI Research Agent</p>
          </div>
        </div>

        {/* Company chip */}
        {showActions && companySetup && config && (
          <>
            <div className="topbar-divider" aria-hidden="true" />
            <div className="topbar-company-chip" aria-label={`Analyzing ${companySetup.name}`}>
              <Building2 size={16} style={{ color: '#2BB5D4', flexShrink: 0 }} strokeWidth={1.5} aria-hidden="true" />
              <div className="topbar-company-chip-text">
                <span className="topbar-company-name">{companySetup.name}</span>
                <span className="topbar-company-role">{config.title}</span>
              </div>
              <a
                href={companySetup.url || ({
                  'Apple Inc.': 'https://investor.apple.com',
                  'JPMorgan Chase & Co.': 'https://www.jpmorganchase.com/ir',
                  'Pfizer Inc.': 'https://www.pfizer.com/investors',
                  'ExxonMobil Corporation': 'https://corporate.exxonmobil.com/investors',
                  'Amazon Inc.': 'https://ir.aboutamazon.com',
                } as Record<string, string>)[companySetup.name] || `https://www.google.com/search?q=${encodeURIComponent(companySetup.name + ' investor relations')}`}
                target="_blank"
                rel="noopener noreferrer"
                className="topbar-company-link"
                aria-label={`Open website for ${companySetup.name} (opens in new tab)`}
              >
                <ExternalLink size={12} strokeWidth={1.5} />
              </a>
            </div>
          </>
        )}

        {/* Scenario dropdown */}
        {showScenarioDropdown && (
          <>
            <div className="topbar-divider" aria-hidden="true" />
            <div className="topbar-relative" ref={scenarioRef}>
              <button
                className={`topbar-action-btn ${activeScenario ? 'topbar-action-btn--active' : ''}`}
                onClick={() => setScenarioOpen(!scenarioOpen)}
                aria-expanded={scenarioOpen}
                aria-haspopup="listbox"
                aria-label="Select scenario"
              >
                <FlaskConical size={14} strokeWidth={1.5} aria-hidden="true" />
                {activeScenario ? activeScenario.shortName : 'Select Scenario'}
                <ChevronDown size={12} style={{ transform: scenarioOpen ? 'rotate(180deg)' : undefined, transition: 'transform 0.15s' }} strokeWidth={1.5} aria-hidden="true" />
              </button>
              {scenarioOpen && (
                <div className="topbar-profile-dropdown" role="listbox" aria-label="Scenario options" style={{ width: '18rem' }}>
                  <button
                    role="option"
                    aria-selected={!activeScenario}
                    className={`topbar-dropdown-item ${!activeScenario ? 'topbar-dropdown-item--active' : ''}`}
                    onClick={() => { setScenarioOpen(false); onSetScenario?.(null); toast.success('Switched to default view'); }}
                  >
                    {!activeScenario && <Check size={14} style={{ color: '#2BB5D4' }} aria-hidden="true" />}
                    <span style={{ marginLeft: !activeScenario ? 0 : '1.375rem' }}>Default</span>
                  </button>
                  <div className="topbar-dropdown-sep" aria-hidden="true" />
                  {availableScenarios.map((scenario) => (
                    <button
                      key={scenario.id}
                      role="option"
                      aria-selected={activeScenario?.id === scenario.id}
                      className={`topbar-dropdown-item ${activeScenario?.id === scenario.id ? 'topbar-dropdown-item--active' : ''}`}
                      onClick={() => { setScenarioOpen(false); onSetScenario?.(scenario.id); toast.success(`Switched to ${scenario.name}`); }}
                      style={{ flexDirection: 'column', alignItems: 'flex-start', gap: '0.125rem' }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        {activeScenario?.id === scenario.id && <Check size={14} style={{ color: '#2BB5D4' }} aria-hidden="true" />}
                        <span style={{ marginLeft: activeScenario?.id === scenario.id ? 0 : '1.375rem', fontWeight: 500 }}>{scenario.name}</span>
                      </div>
                      <span style={{ fontSize: '0.625rem', color: '#64748b', marginLeft: '1.375rem' }}>{scenario.description}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </>
        )}
      </div>

      {/* Right actions */}
      <nav className="topbar-right" aria-label="Toolbar actions">
        {showActions && (
          <>
            <button className="topbar-action-btn" onClick={onNewConversation} aria-label="Start new conversation">
              <RotateCcw size={14} strokeWidth={1.5} aria-hidden="true" />
              New Chat
            </button>
            <button
              className={`topbar-action-btn ${citationPanelOpen ? 'topbar-action-btn--active' : ''}`}
              onClick={onToggleCitationPanel}
              aria-pressed={citationPanelOpen}
              aria-label={citationPanelOpen ? 'Close sources panel' : 'Open sources panel'}
            >
              <BookOpen size={14} strokeWidth={1.5} aria-hidden="true" />
              Sources
            </button>
            <div className="topbar-relative" ref={exportRef}>
              <button
                className="topbar-action-btn"
                onClick={() => setExportOpen(!exportOpen)}
                aria-expanded={exportOpen}
                aria-haspopup="menu"
                aria-label="Export options"
              >
                <Download size={14} strokeWidth={1.5} aria-hidden="true" />
                Export
              </button>
              {exportOpen && (
                <div className="topbar-profile-dropdown" role="menu" aria-label="Export options" style={{ width: '13rem' }}>
                  <button role="menuitem" className="topbar-dropdown-item"
                    onClick={() => {
                      const last = [...messages].reverse().find((m) => m.role === 'assistant');
                      if (!last) { toast.error('No AI response to copy'); return; }
                      navigator.clipboard.writeText(last.content.replace(/\{\{cit:[^}]+\}\}/g, ''));
                      setCopied(true); setTimeout(() => setCopied(false), 2000);
                      toast.success('Response copied to clipboard'); setExportOpen(false);
                    }} disabled={!messages.length}>
                    {copied ? <Check size={14} style={{ color: '#4ade80' }} aria-hidden="true" /> : <Copy size={14} strokeWidth={1.5} aria-hidden="true" />}
                    Copy Last Response
                  </button>
                  <button role="menuitem" className="topbar-dropdown-item"
                    onClick={() => { handleExportPDF(); setExportOpen(false); }} disabled={!messages.length}>
                    <FileText size={14} strokeWidth={1.5} aria-hidden="true" />
                    Export as PDF
                  </button>
                  <button role="menuitem" className="topbar-dropdown-item"
                    onClick={() => {
                      const data = { exportedAt: new Date().toISOString(), messages: messages.map((m) => ({ role: m.role, content: m.content.replace(/\{\{cit:[^}]+\}\}/g, ''), timestamp: m.timestamp })) };
                      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
                      const url = URL.createObjectURL(blob);
                      const a = document.createElement('a'); a.href = url;
                      a.download = `deal-intelligence-${new Date().toISOString().slice(0, 10)}.json`; a.click();
                      URL.revokeObjectURL(url); toast.success('Conversation saved as JSON'); setExportOpen(false);
                    }} disabled={!messages.length}>
                    <Save size={14} strokeWidth={1.5} aria-hidden="true" />
                    Save Conversation
                  </button>
                  <div className="topbar-dropdown-sep" aria-hidden="true" />
                  <button role="menuitem" className="topbar-dropdown-item"
                    onClick={() => {
                      navigator.clipboard.writeText(`https://deal-intel.app/shared/${Date.now().toString(36)}`);
                      toast.success('Share link copied to clipboard'); setExportOpen(false);
                    }} disabled={!messages.length}>
                    <Share2 size={14} strokeWidth={1.5} aria-hidden="true" />
                    Copy Share Link
                  </button>
                </div>
              )}
            </div>
            <div className="topbar-divider" aria-hidden="true" />
          </>
        )}

        {/* Profile dropdown */}
        {activePersona && profile && (
          <div className="topbar-relative" ref={profileRef}>
            <button
              className="topbar-profile-btn"
              onClick={() => setProfileOpen(!profileOpen)}
              aria-expanded={profileOpen}
              aria-haspopup="menu"
              aria-label={`Profile menu for ${profile.name}`}
            >
              <img src={profile.photo} alt={profile.name} className="topbar-profile-avatar" />
              <div style={{ textAlign: 'left' }}>
                <p className="topbar-profile-name">{profile.name}</p>
                <p className="topbar-profile-role">{activePersona.name}</p>
              </div>
              <ChevronDown size={12} style={{ color: '#475569', transform: profileOpen ? 'rotate(180deg)' : undefined, transition: 'transform 0.15s' }} strokeWidth={1.5} aria-hidden="true" />
            </button>

            {profileOpen && (
              <div className="topbar-profile-dropdown" role="menu" aria-label="Profile options">
                <div className="topbar-profile-info">
                  <p className="topbar-profile-info-name">{profile.name}</p>
                  <p className="topbar-profile-info-role">{activePersona.name}</p>
                </div>
                <div className="topbar-dropdown-sep" aria-hidden="true" />
                {onBackToLanding && (
                  <button role="menuitem" className="topbar-dropdown-item" onClick={() => { setProfileOpen(false); onBackToLanding(); }}>
                    <ArrowLeft size={14} strokeWidth={1.5} aria-hidden="true" />
                    Back to Analyses
                  </button>
                )}
                {onSignOut && (
                  <button role="menuitem" className="topbar-dropdown-item" onClick={() => { setProfileOpen(false); onSignOut(); }}>
                    <LogOut size={14} strokeWidth={1.5} aria-hidden="true" />
                    Sign Out
                  </button>
                )}
              </div>
            )}
          </div>
        )}
      </nav>
    </header>
  );
}
