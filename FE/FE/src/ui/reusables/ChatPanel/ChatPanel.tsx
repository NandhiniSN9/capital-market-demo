import { useState, useMemo, useRef, useEffect, RefObject } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import { Sparkles, ArrowUp, Loader2, Calculator, FileText, AlertTriangle, ChevronDown, ChevronRight } from 'lucide-react';
import { MessageBO, CitationBO } from '../../../types/chat/ChatBO.ts';
import { PersonaBO, CompanySetupBO, SimulationBO } from '../../../types/persona/PersonaBO.ts';
import { type ScenarioDefinition } from '../../../helpers/data/scenarioConfig.ts';
import { getPersonaConfig, ICON_COMPONENT_MAP } from '../../../helpers/data/personaConfig.ts';
import { getPersonaPhoto } from '../../../helpers/data/personaProfiles.ts';
import './ChatPanel.css';

interface ChatPanelProps {
  messages: MessageBO[];
  isStreaming: boolean;
  streamingMessageId: string | null;
  scrollRef: RefObject<HTMLDivElement | null>;
  activePersona: PersonaBO;
  activeSimulation: SimulationBO | null;
  activeScenario?: ScenarioDefinition | null;
  companySetup: CompanySetupBO | null;
  inputValue: string;
  onInputChange: (v: string) => void;
  onSendQuestion: (q: string) => void;
  onOpenDocument: (opts: { documentId: string; page: number; highlightText?: string; citationId?: string; section?: string }) => void;
}

const CIT_COLORS: Record<string, { bg: string; text: string }> = {
  '10-K': { bg: 'rgba(59,130,246,0.15)', text: '#93c5fd' },
  '10-Q': { bg: 'rgba(6,182,212,0.15)', text: '#67e8f9' },
  'Earnings Call': { bg: 'rgba(245,158,11,0.15)', text: '#fcd34d' },
  'Credit Agreement': { bg: 'rgba(168,85,247,0.15)', text: '#d8b4fe' },
};

function CitationChip({ citation, onOpen }: { citation: CitationBO; onOpen: () => void }) {
  const [showTooltip, setShowTooltip] = useState(false);
  const colors = CIT_COLORS[citation.shortName] ?? { bg: 'rgba(100,116,139,0.15)', text: '#94a3b8' };
  return (
    <span style={{ position: 'relative', display: 'inline-block' }}>
      <button
        className="cit-chip"
        style={{ backgroundColor: colors.bg, color: colors.text }}
        onClick={onOpen}
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
        onFocus={() => setShowTooltip(true)}
        onBlur={() => setShowTooltip(false)}
        aria-label={`Citation: ${citation.documentName}, page ${citation.page}`}
      >
        {citation.label}
      </button>
      {showTooltip && (
        <div className="cit-tooltip" role="tooltip">
          <p className="cit-tooltip-doc">{citation.documentName}</p>
          <p className="cit-tooltip-meta">{citation.section} · Page {citation.page}</p>
          <p className="cit-tooltip-quote">"{citation.exactQuote}"</p>
          <p className="cit-tooltip-hint">Click to view in document</p>
        </div>
      )}
    </span>
  );
}

function AIMessage({ message, isStreaming, onOpenDocument, onSendQuestion }: {
  message: MessageBO;
  isStreaming: boolean;
  onOpenDocument: ChatPanelProps['onOpenDocument'];
  onSendQuestion: (q: string) => void;
}) {
  const [showCalc, setShowCalc] = useState(false);
  const [showSources, setShowSources] = useState(false);
  const [showAssumptions, setShowAssumptions] = useState(false);

  const citationMap = useMemo(() => {
    const m = new Map<string, CitationBO>();
    message.citations?.forEach((c) => m.set(c.id, c));
    return m;
  }, [message.citations]);

  const renderContent = (content: string) => {
    // Empty bubble while waiting for first token — show thinking indicator
    if (!content && isStreaming) {
      return (
        <div className="chat-thinking" aria-label="Generating response">
          <div className="chat-thinking-dot" style={{ animationDelay: '0ms' }} aria-hidden="true" />
          <div className="chat-thinking-dot" style={{ animationDelay: '150ms' }} aria-hidden="true" />
          <div className="chat-thinking-dot" style={{ animationDelay: '300ms' }} aria-hidden="true" />
        </div>
      );
    }

    // Remove "Suggested Questions" section from content since we render it separately as tiles
    let cleanedContent = content;
    const suggestedQuestionsRegex = /\n*(?:Suggested Questions?|Related Questions?):?\s*\n[\s\S]*$/i;
    cleanedContent = cleanedContent.replace(suggestedQuestionsRegex, '').trim();

    // Strip agent metadata markers that appear during streaming
    // These get parsed into structured UI elements after stream completes
    cleanedContent = cleanedContent
      .replace(/\n*CALCULATIONS_JSON:\s*\[[\s\S]*?(?:\]|$)/i, '')
      .replace(/\n*ASSUMPTIONS:\s*\[[\s\S]*?(?:\]|$)/i, '')
      .replace(/\n*CONFIDENCE:\s*(?:high|medium|low)\s*/i, '')
      .replace(/\n*CONFIDENCE_REASON:\s*[^\n]*/i, '')
      .replace(/\n*SESSION_TITLE:\s*[^\n]*/i, '')
      .trim();

    const citRegex = /\{\{cit:([^}]+)\}\}/g;
    const segments: Array<{ type: 'text' | 'cit'; value: string }> = [];
    let last = 0; let match;
    while ((match = citRegex.exec(cleanedContent)) !== null) {
      if (match.index > last) segments.push({ type: 'text', value: cleanedContent.slice(last, match.index) });
      segments.push({ type: 'cit', value: match[1] });
      last = match.index + match[0].length;
    }
    if (last < cleanedContent.length) segments.push({ type: 'text', value: cleanedContent.slice(last) });

    if (segments.length === 1 && segments[0].type === 'text') {
      return (
        <div className={`ai-response text-sm text-slate-300${isStreaming ? ' streaming-cursor' : ''}`}>
          <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeRaw]}>{cleanedContent}</ReactMarkdown>
        </div>
      );
    }

    return (
      <div className={`ai-response text-sm text-slate-300${isStreaming ? ' streaming-cursor' : ''}`}>
        {segments.map((seg, i) => {
          if (seg.type === 'cit') {
            const cit = citationMap.get(seg.value);
            if (!cit) return null;
            return (
              <CitationChip
                key={i}
                citation={cit}
                onOpen={() => onOpenDocument({ documentId: cit.documentId, page: cit.page, highlightText: cit.exactQuote, citationId: cit.id, section: cit.section })}
              />
            );
          }
          if (!seg.value.trim()) return null;
          return <ReactMarkdown key={i} remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeRaw]}>{seg.value}</ReactMarkdown>;
        })}
      </div>
    );
  };

  const confidenceConfig = {
    high: { label: 'High Confidence', color: '#4ade80', bg: 'rgba(34,197,94,0.05)', border: 'rgba(34,197,94,0.1)', dots: 3 },
    medium: { label: 'Medium Confidence', color: '#fbbf24', bg: 'rgba(245,158,11,0.05)', border: 'rgba(245,158,11,0.1)', dots: 2 },
    low: { label: 'Low Confidence', color: '#f87171', bg: 'rgba(239,68,68,0.05)', border: 'rgba(239,68,68,0.1)', dots: 1 },
  };
  const conf = message.confidence ? confidenceConfig[message.confidence] : null;

  return (
    <div className="chat-msg-ai" role="article" aria-label="AI response">
      <div className="chat-msg-ai-icon" aria-hidden="true">
        <Sparkles size={14} style={{ color: '#2BB5D4' }} strokeWidth={1.5} />
      </div>
      <div className="chat-msg-ai-body">
        <div className="chat-msg-ai-bubble">
          {renderContent(message.content)}
          {!isStreaming && message.citations && message.citations.length > 0 && (
            <div className="chat-citations-row" aria-label="Citations">
              {message.citations.map((cit) => (
                <CitationChip
                  key={cit.id}
                  citation={cit}
                  onOpen={() => onOpenDocument({ documentId: cit.documentId, page: cit.page, highlightText: cit.exactQuote, citationId: cit.id, section: cit.section })}
                />
              ))}
            </div>
          )}
        </div>

        {!isStreaming && conf && (
          <div className="chat-confidence" style={{ backgroundColor: conf.bg, borderColor: conf.border }}>
            <div className="chat-confidence-dots" aria-hidden="true">
              {[1, 2, 3].map((i) => (
                <div key={i} className="chat-confidence-dot" style={{ backgroundColor: i <= conf.dots ? conf.color : '#1e293b' }} />
              ))}
            </div>
            <span className="chat-confidence-label" style={{ color: conf.color }}>{conf.label}</span>
            <span className="chat-confidence-sep" aria-hidden="true">·</span>
            <span className="chat-confidence-reason">{message.confidenceReason}</span>
          </div>
        )}

        {!isStreaming && (
          <div className="chat-expand-btns">
            {message.calculations && message.calculations.length > 0 && (
              <button className="chat-expand-btn" onClick={() => setShowCalc(!showCalc)} aria-expanded={showCalc} aria-controls={`calc-${message.id}`}>
                <Calculator size={12} aria-hidden="true" />
                Calculations
                {showCalc ? <ChevronDown size={12} aria-hidden="true" /> : <ChevronRight size={12} aria-hidden="true" />}
              </button>
            )}
            {message.sourceExcerpts && message.sourceExcerpts.length > 0 && (
              <button className="chat-expand-btn" onClick={() => setShowSources(!showSources)} aria-expanded={showSources} aria-controls={`sources-${message.id}`}>
                <FileText size={12} aria-hidden="true" />
                Source Text
                {showSources ? <ChevronDown size={12} aria-hidden="true" /> : <ChevronRight size={12} aria-hidden="true" />}
              </button>
            )}
            {message.assumptions && message.assumptions.length > 0 && (
              <button className="chat-expand-btn" onClick={() => setShowAssumptions(!showAssumptions)} aria-expanded={showAssumptions} aria-controls={`assumptions-${message.id}`}>
                <AlertTriangle size={12} aria-hidden="true" />
                Assumptions
                {showAssumptions ? <ChevronDown size={12} aria-hidden="true" /> : <ChevronRight size={12} aria-hidden="true" />}
              </button>
            )}
          </div>
        )}

        {showCalc && message.calculations && (
          <div id={`calc-${message.id}`} className="chat-expand-panel">
            {message.calculations.map((c, i) => (
              <div key={i} style={{ marginBottom: i < message.calculations!.length - 1 ? '0.75rem' : 0 }}>
                <p className="chat-calc-title">{c.title}</p>
                <div className="chat-calc-steps">{c.steps}</div>
                <p className="chat-calc-result">{c.result.replace(/\*\*/g, '')}</p>
              </div>
            ))}
          </div>
        )}

        {showSources && message.sourceExcerpts && (
          <div id={`sources-${message.id}`} className="chat-expand-panel">
            {message.sourceExcerpts.map((s, i) => (
              <div key={i} className="chat-source-item">
                <p className="chat-source-quote">"{s.text}"</p>
                <p className="chat-source-ctx">{s.context}</p>
              </div>
            ))}
          </div>
        )}

        {showAssumptions && message.assumptions && (
          <div id={`assumptions-${message.id}`} className="chat-expand-panel" style={{ border: '1px solid rgba(245,158,11,0.1)', backgroundColor: 'rgba(245,158,11,0.05)' }}>
            {message.assumptions.map((a, i) => (
              <div key={i} className="chat-assumption-item">
                <span className="chat-assumption-dot" aria-hidden="true" />
                {a}
              </div>
            ))}
          </div>
        )}

        {!isStreaming && message.relatedQuestions && message.relatedQuestions.length > 0 && (
          <div className="chat-related">
            <div className="chat-related-header">
              <Sparkles size={12} style={{ color: '#38bdf8' }} aria-hidden="true" />
              Related questions
            </div>
            <div className="chat-related-btns">
              {message.relatedQuestions.slice(0, 4).map((q, i) => (
                <button key={i} className="chat-related-btn" onClick={() => onSendQuestion(q)}>
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export function ChatPanel({
  messages, isStreaming, streamingMessageId, scrollRef,
  activePersona, activeSimulation, activeScenario, companySetup,
  inputValue, onInputChange, onSendQuestion, onOpenDocument,
}: ChatPanelProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const config = getPersonaConfig(activePersona.id);
  const IconComponent = ICON_COMPONENT_MAP[activePersona.icon];
  const profilePhoto = getPersonaPhoto(activePersona.id);

  // Priority: activeScenario > activeSimulation > persona defaults
  const questions = activeScenario
    ? activeScenario.suggestedQuestions
    : activeSimulation
      ? activeSimulation.suggestedQuestions
      : activePersona.suggestedQuestions.slice(0, 4);

  const welcomeTitle = activeScenario
    ? activeScenario.name
    : activeSimulation
      ? activeSimulation.name
      : `Welcome to ${activePersona.name.replace(/\s*Analyst$/, '')} Deal Intelligence`;

  const welcomeSubtitle = activeScenario
    ? activeScenario.description
    : activeSimulation
      ? activeSimulation.description
      : config.welcomeHelpText;

  const suggestedLabel = activeScenario?.shortName ?? activeSimulation?.shortName ?? activePersona.name;

  useEffect(() => { textareaRef.current?.focus(); }, []);

  useEffect(() => {
    const el = textareaRef.current;
    if (el) { el.style.height = 'auto'; el.style.height = Math.min(el.scrollHeight, 120) + 'px'; }
  }, [inputValue]);

  const handleSend = () => {
    if (!inputValue.trim() || isStreaming) return;
    onSendQuestion(inputValue.trim());
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); }
  };

  return (
    <div className="chat-panel">
      <div ref={scrollRef} className="chat-panel-messages" role="log" aria-live="polite" aria-label="Conversation">
        {messages.length === 0 ? (
          <div className="chat-welcome">
            <div className="chat-welcome-inner">
              <div className="chat-welcome-icon-wrap" aria-hidden="true">
                {IconComponent && <IconComponent className="h-7 w-7 text-[#ff5f46]" />}
              </div>
              <h2 className="chat-welcome-title">{welcomeTitle}</h2>
              <p className="chat-welcome-subtitle">{welcomeSubtitle}</p>
              <div>
                <div className="chat-welcome-suggestions-label">
                  <Sparkles size={14} style={{ color: '#2BB5D4' }} aria-hidden="true" />
                  Suggested for {suggestedLabel}
                </div>
                <div className="chat-welcome-suggestions">
                  {questions.map((q, i) => (
                    <button key={i} className="chat-welcome-suggestion-btn" onClick={() => onSendQuestion(q)}>
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="chat-panel-messages-inner">
            {messages.map((msg) => {
              if (msg.role === 'user') {
                return (
                  <div key={msg.id} className="chat-msg-user" role="article" aria-label="Your message">
                    <div className="chat-msg-user-inner">
                      <div className="chat-msg-user-bubble">
                        <p className="chat-msg-user-text">{msg.content}</p>
                      </div>
                      <img src={profilePhoto} alt="You" className="chat-msg-user-avatar" />
                    </div>
                  </div>
                );
              }
              return (
                <AIMessage
                  key={msg.id}
                  message={msg}
                  isStreaming={isStreaming && streamingMessageId === msg.id}
                  onOpenDocument={onOpenDocument}
                  onSendQuestion={onSendQuestion}
                />
              );
            })}
            {isStreaming && (
              <span className="sr-only" aria-live="polite">AI is responding</span>
            )}
          </div>
        )}
      </div>

      {/* Input */}
      <div className="chat-input-area">
        <div className="chat-input-inner">
          <div className="chat-input-box">
            <label htmlFor="chat-input" className="sr-only">Ask a question about the documents</label>
            <textarea
              id="chat-input"
              ref={textareaRef}
              value={inputValue}
              onChange={(e) => onInputChange(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question about the documents..."
              disabled={isStreaming}
              rows={1}
              className="chat-input-textarea"
              aria-label="Chat input"
            />
            <button
              className="chat-input-send"
              onClick={handleSend}
              disabled={!inputValue.trim() || isStreaming}
              aria-label="Send message"
            >
              {isStreaming
                ? <Loader2 size={16} className="animate-spin" strokeWidth={1.5} aria-hidden="true" />
                : <ArrowUp size={16} strokeWidth={2} aria-hidden="true" />}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
 