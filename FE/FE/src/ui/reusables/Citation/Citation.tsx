import { useState } from 'react';
import { CitationBO as CitationType } from '@/types/chat/ChatBO.ts';
import { useUIStore } from '@/store/uiStore';
import { cn } from '@/helpers/utilities/utils';

interface CitationProps {
  citation: CitationType;
  variant?: 'inline' | 'compact';
}

const docColors: Record<string, { bg: string; text: string; hover: string }> = {
  '10-K': { bg: 'bg-blue-500/10', text: 'text-blue-400', hover: 'hover:bg-blue-500/20' },
  '10-Q': { bg: 'bg-cyan-500/10', text: 'text-cyan-400', hover: 'hover:bg-cyan-500/20' },
  'Earnings Call': { bg: 'bg-amber-500/10', text: 'text-amber-400', hover: 'hover:bg-amber-500/20' },
  'Credit Agreement': { bg: 'bg-purple-500/10', text: 'text-purple-400', hover: 'hover:bg-purple-500/20' },
};

export function Citation({ citation, variant = 'inline' }: CitationProps) {
  const [showTooltip, setShowTooltip] = useState(false);
  const openDocumentViewer = useUIStore((s) => s.openDocumentViewer);

  const colors = docColors[citation.shortName] || { bg: 'bg-slate-500/10', text: 'text-slate-400', hover: 'hover:bg-slate-500/20' };

  const handleClick = () => {
    openDocumentViewer({
      documentId: citation.documentId,
      page: citation.page,
      highlightText: citation.exactQuote,
      citationId: citation.id,
      section: citation.section,
    });
  };

  return (
    <span className="relative inline-block">
      <button
        onClick={handleClick}
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
        className={cn(
          'inline-flex items-center rounded-full px-1.5 py-0 text-[10px] font-medium cursor-pointer transition-all',
          colors.bg,
          colors.text,
          colors.hover,
          variant === 'compact' && 'px-2 py-0.5'
        )}
      >
        {citation.label}
      </button>

      {/* Tooltip */}
      {showTooltip && (
        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 z-50 w-72 rounded-lg border border-slate-700 bg-slate-900 p-3 shadow-xl shadow-black/50 pointer-events-none">
          <p className="text-[10px] font-semibold text-sky-400 mb-1">{citation.documentName}</p>
          <p className="text-[10px] text-slate-500 mb-2">
            {citation.section} &middot; Page {citation.page}
          </p>
          <p className="text-[11px] text-slate-300 italic leading-relaxed line-clamp-3">
            "{citation.exactQuote}"
          </p>
          <p className="mt-1.5 text-[9px] text-slate-600">Click to view in document</p>
        </div>
      )}
    </span>
  );
}
