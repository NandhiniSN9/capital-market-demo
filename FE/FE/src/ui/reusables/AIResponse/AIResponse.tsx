import { useState, useMemo, Fragment } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import { Sparkles, ChevronDown, ChevronRight, Calculator, FileText, AlertTriangle } from 'lucide-react';
import { MessageBO as Message, CitationBO as CitationType } from '@/types/chat/ChatBO.ts';
import { Citation } from '@/ui/reusables/Citation/Citation';
import { ConfidenceIndicator } from '@/ui/reusables/ConfidenceIndicator/ConfidenceIndicator';
import { RelatedQuestions } from '@/ui/reusables/RelatedQuestions/RelatedQuestions';
import { useChatStore } from '@/store/chatStore';
import { cn } from '@/helpers/utilities/utils';
import { motion, AnimatePresence } from 'framer-motion';

interface AIResponseProps {
  message: Message;
  isStreaming: boolean;
}

export function AIResponse({ message, isStreaming }: AIResponseProps) {
  const [showCalculations, setShowCalculations] = useState(false);
  const [showSources, setShowSources] = useState(false);
  const [showAssumptions, setShowAssumptions] = useState(false);
  const streamingStatus = useChatStore((s) => s.streamingStatus);

  // Build a citation map for quick lookup
  const citationMap = useMemo(() => {
    const map = new Map<string, CitationType>();
    message.citations?.forEach((c) => map.set(c.id, c));
    return map;
  }, [message.citations]);

  // Preprocess content: replace [docName, p.XX] or [docId, p.XX] with {{cit:id}} tokens
  const processedContent = useMemo(() => {
    if (!message.content || !message.citations?.length) return message.content;

    let text = message.content;
    // Match patterns like [48c4949d, p.52] or [10-K_2024-02-22.pdf, p.52]
    const inlineRef = /\[([^\]]+?),\s*p\.(\d+)\]/g;

    text = text.replace(inlineRef, (fullMatch, nameOrId: string, pageStr: string) => {
      const page = parseInt(pageStr, 10);
      const trimmed = nameOrId.trim();

      // Find matching citation by documentName/shortName/documentId + page
      const match = message.citations!.find((c) => {
        const pageMatch = c.page === page;
        return pageMatch && (
          c.documentName === trimmed ||
          c.shortName === trimmed ||
          c.documentId === trimmed ||
          c.documentId.startsWith(trimmed)
        );
      });

      return match ? `{{cit:${match.id}}}` : fullMatch;
    });

    return text;
  }, [message.content, message.citations]);

  // Split content into text segments and citation components
  const renderContentWithCitations = (content: string) => {
    // Split on {{cit:xxx}} tokens
    const citRegex = /\{\{cit:([^}]+)\}\}/g;
    const segments: Array<{ type: 'text' | 'citation'; value: string }> = [];
    let lastIndex = 0;
    let match;

    while ((match = citRegex.exec(content)) !== null) {
      if (match.index > lastIndex) {
        segments.push({ type: 'text', value: content.slice(lastIndex, match.index) });
      }
      segments.push({ type: 'citation', value: match[1] });
      lastIndex = match.index + match[0].length;
    }
    if (lastIndex < content.length) {
      segments.push({ type: 'text', value: content.slice(lastIndex) });
    }

    // Clean up text segments that follow citations:
    // Strip leading punctuation (like ". " or ".\n") that was part of the sentence before the citation
    const mergedSegments: typeof segments = [];
    for (let i = 0; i < segments.length; i++) {
      const seg = segments[i];
      if (seg.type === 'text' && i > 0 && segments[i - 1].type === 'citation') {
        // Strip leading punctuation + whitespace that follows a citation
        const cleaned = seg.value.replace(/^[.,;:!?)\]}\s]*(?=\S|$)/, '');
        if (cleaned.trim().length > 0) {
          mergedSegments.push({ type: 'text', value: cleaned });
        }
        // If nothing left after stripping, skip the segment entirely
      } else {
        mergedSegments.push({ ...seg });
      }
    }

    // If no citations found, render entire content as markdown
    if (mergedSegments.length === 1 && mergedSegments[0].type === 'text') {
      return (
        <div className={cn('ai-response text-sm text-slate-300', isStreaming && 'streaming-cursor')}>
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            rehypePlugins={[rehypeRaw]}
            components={markdownComponents}
          >
            {content}
          </ReactMarkdown>
        </div>
      );
    }

    // Group consecutive text segments into markdown blocks, interspersing citations
    return (
      <div className={cn('ai-response text-sm text-slate-300', isStreaming && 'streaming-cursor')}>
        {mergedSegments.map((seg, i) => {
          if (seg.type === 'citation') {
            const cit = citationMap.get(seg.value);
            if (cit) {
              return <Citation key={`cit-${i}`} citation={cit} />;
            }
            return null;
          }
          // Skip empty text segments
          if (!seg.value.trim()) return null;
          // Render text as markdown
          return (
            <ReactMarkdown
              key={`md-${i}`}
              remarkPlugins={[remarkGfm]}
              rehypePlugins={[rehypeRaw]}
              components={markdownComponents}
            >
              {seg.value}
            </ReactMarkdown>
          );
        })}
      </div>
    );
  };

  const markdownComponents = {
    p: ({ children }: any) => <p className="mb-2 leading-relaxed">{children}</p>,
    li: ({ children }: any) => <li className="leading-relaxed">{children}</li>,
    table: ({ children }: any) => (
      <div className="overflow-x-auto my-3 rounded-lg border border-slate-800">
        <table className="w-full">{children}</table>
      </div>
    ),
    th: ({ children }: any) => (
      <th className="bg-slate-800/80 px-3 py-2 text-left text-[11px] font-semibold text-slate-300 border-b border-slate-700">
        {children}
      </th>
    ),
    td: ({ children }: any) => (
      <td className="px-3 py-2 text-[11px] text-slate-400 border-b border-slate-800/50 font-mono">
        {children}
      </td>
    ),
  };

  return (
    <div className="flex items-start gap-2.5">
      <div className="flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full bg-[#145D70]/15 mt-0.5">
        <Sparkles className="h-3.5 w-3.5 text-[#2BB5D4] stroke-[1.5]" />
      </div>

      <div className="flex-1 min-w-0 space-y-3">
        {/* Main content */}
        <div className="rounded-2xl rounded-tl-sm bg-slate-900/80 border border-slate-800 px-4 py-3">
          {/* Status indicator while agent is working */}
          {isStreaming && streamingStatus && (
            <div className="flex items-center gap-2 text-xs text-slate-400 mb-2">
              <span className="inline-block h-1.5 w-1.5 rounded-full bg-sky-400 animate-pulse" />
              {streamingStatus}
            </div>
          )}
          {renderContentWithCitations(processedContent)}

          {/* Inline citations list */}
          {!isStreaming && message.citations && message.citations.length > 0 && (
            <div className="mt-3 pt-3 border-t border-slate-800">
              <div className="flex flex-wrap gap-1.5">
                {message.citations.map((cit) => (
                  <Citation key={cit.id} citation={cit} variant="compact" />
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Metadata section (after streaming completes) */}
        {!isStreaming && (
          <div className="space-y-2">
            {/* Confidence */}
            <ConfidenceIndicator
              level={message.confidence || 'medium'}
              reason={message.confidenceReason || 'Confidence level not provided by agent'}
            />

            {/* Expandable sections — always visible */}
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => setShowCalculations(!showCalculations)}
                className="flex items-center gap-1.5 rounded-md border border-[#145D70]/50 bg-[#145D70] px-2.5 py-1.5 text-[11px] text-white hover:bg-[#1A7A92] transition-colors"
              >
                <Calculator className="h-3 w-3 stroke-[1.5]" />
                Show Calculations
                {showCalculations ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
              </button>

              <button
                onClick={() => setShowSources(!showSources)}
                className="flex items-center gap-1.5 rounded-md border border-[#145D70]/50 bg-[#145D70] px-2.5 py-1.5 text-[11px] text-white hover:bg-[#1A7A92] transition-colors"
              >
                <FileText className="h-3 w-3 stroke-[1.5]" />
                View Source Text
                {showSources ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
              </button>

              <button
                onClick={() => setShowAssumptions(!showAssumptions)}
                className="flex items-center gap-1.5 rounded-md border border-[#145D70]/50 bg-[#145D70] px-2.5 py-1.5 text-[11px] text-white hover:bg-[#1A7A92] transition-colors"
              >
                <AlertTriangle className="h-3 w-3 stroke-[1.5]" />
                Assumptions
                {showAssumptions ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
              </button>
            </div>

            {/* Calculations panel */}
            <AnimatePresence>
              {showCalculations && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  className="overflow-hidden"
                >
                  <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-3 space-y-3">
                    {message.calculations && message.calculations.length > 0 ? (
                      message.calculations.map((calc, i) => (
                        <div key={i}>
                          <h4 className="text-[11px] font-semibold text-sky-400 mb-1.5">{calc.title}</h4>
                          <div className="rounded-md bg-slate-950/50 p-2.5 font-mono text-[11px] text-slate-400 whitespace-pre-line leading-relaxed">
                            {calc.steps}
                          </div>
                          <div className="mt-1.5 text-xs font-semibold text-emerald-400">
                            {calc.result.replace(/\*\*/g, '')}
                          </div>
                        </div>
                      ))
                    ) : (
                      <p className="text-[11px] text-slate-500 italic">No calculations available for this response.</p>
                    )}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Source text panel */}
            <AnimatePresence>
              {showSources && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  className="overflow-hidden"
                >
                  <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-3 space-y-3">
                    {message.sourceExcerpts && message.sourceExcerpts.length > 0 ? (
                      message.sourceExcerpts.map((excerpt, i) => (
                        <div key={i} className="border-l-2 border-sky-500/30 pl-3">
                          <p className="text-xs text-slate-300 italic leading-relaxed">
                            &ldquo;{excerpt.text}&rdquo;
                          </p>
                          <p className="mt-1 text-[10px] text-slate-500">{excerpt.context}</p>
                        </div>
                      ))
                    ) : (
                      <p className="text-[11px] text-slate-500 italic">No source excerpts available for this response.</p>
                    )}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Assumptions panel */}
            <AnimatePresence>
              {showAssumptions && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  className="overflow-hidden"
                >
                  <div className="rounded-lg border border-amber-500/10 bg-amber-500/5 p-3">
                    {message.assumptions && message.assumptions.length > 0 ? (
                      <ul className="space-y-1">
                        {message.assumptions.map((a, i) => (
                          <li key={i} className="flex items-start gap-2 text-[11px] text-amber-200/70">
                            <span className="mt-1 h-1 w-1 rounded-full bg-amber-500/50 flex-shrink-0" />
                            {a}
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="text-[11px] text-slate-500 italic">No assumptions noted for this response.</p>
                    )}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Related questions */}
            {message.relatedQuestions && message.relatedQuestions.length > 0 && (
              <RelatedQuestions questions={message.relatedQuestions} />
            )}
          </div>
        )}
      </div>
    </div>
  );
}
