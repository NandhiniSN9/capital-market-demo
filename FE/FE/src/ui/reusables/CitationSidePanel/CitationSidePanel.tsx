import { BookOpen, FileText, ExternalLink, Download, X } from 'lucide-react';
import { MessageBO, CitationBO } from '../../../types/chat/ChatBO.ts';
import { toast } from 'sonner';
import './CitationSidePanel.css';

interface CitationSidePanelProps {
  messages: MessageBO[];
  onClose: () => void;
  onOpenDocument: (opts: { documentId: string; page: number; highlightText?: string; citationId?: string; section?: string }) => void;
}

export function CitationSidePanel({ messages, onClose, onOpenDocument }: CitationSidePanelProps) {
  // Collect unique citations across all messages
  const allCitations: CitationBO[] = [];
  messages.forEach((m) => {
    m.citations?.forEach((c) => {
      if (!allCitations.find((ac) => ac.id === c.id)) allCitations.push(c);
    });
  });

  // Group by document
  const byDocument = allCitations.reduce<Record<string, CitationBO[]>>((acc, cit) => {
    if (!acc[cit.documentId]) acc[cit.documentId] = [];
    acc[cit.documentId].push(cit);
    return acc;
  }, {});

  const handleExport = () => {
    if (!allCitations.length) { toast.error('No citations to export'); return; }
    const rows = Object.entries(byDocument).map(([, cits]) => {
      const docName = cits[0].documentName;
      const citRows = cits.map((c) => `<tr><td style="padding:8px 12px;border-bottom:1px solid #334155;color:#94a3b8;font-size:12px;">${c.section}</td><td style="padding:8px 12px;border-bottom:1px solid #334155;color:#94a3b8;font-size:12px;text-align:center;">${c.page}</td><td style="padding:8px 12px;border-bottom:1px solid #334155;color:#7d8da6;font-size:11px;font-style:italic;">"${c.exactQuote}"</td></tr>`).join('');
      return `<div style="margin-bottom:24px;"><h3 style="color:#e2e8f0;font-size:14px;font-weight:600;margin:0 0 8px;">${docName}</h3><table style="width:100%;border-collapse:collapse;border:1px solid #334155;"><thead><tr style="background:#1e293b;"><th style="padding:8px 12px;text-align:left;color:#64748b;font-size:11px;border-bottom:1px solid #334155;">Section</th><th style="padding:8px 12px;text-align:center;color:#64748b;font-size:11px;border-bottom:1px solid #334155;">Page</th><th style="padding:8px 12px;text-align:left;color:#64748b;font-size:11px;border-bottom:1px solid #334155;">Quote</th></tr></thead><tbody>${citRows}</tbody></table></div>`;
    }).join('');
    const html = `<!DOCTYPE html><html><head><title>Citations Export</title><style>body{font-family:system-ui;background:#020617;padding:32px;max-width:900px;margin:0 auto;}h1{color:#38bdf8;font-size:18px;}p{color:#64748b;font-size:11px;margin-bottom:24px;}</style></head><body><h1>Deal Intelligence — Citations</h1><p>Exported ${new Date().toLocaleString()} · ${allCitations.length} citations</p>${rows}</body></html>`;
    const w = window.open('', '_blank');
    if (w) { w.document.write(html); w.document.close(); setTimeout(() => w.print(), 500); }
    toast.success('PDF export opened');
  };

  return (
    <aside className="cit-side-panel" aria-label="Citations panel">
      <div className="cit-side-header">
        <div className="cit-side-header-left">
          <BookOpen size={16} style={{ color: '#38bdf8' }} aria-hidden="true" />
          <h2 className="cit-side-title">Sources</h2>
          <span className="cit-side-count" aria-label={`${allCitations.length} citations`}>{allCitations.length}</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
          <button
            className="cit-side-export"
            onClick={handleExport}
            disabled={!allCitations.length}
            aria-label="Export citations as PDF"
          >
            <Download size={14} aria-hidden="true" />
            PDF
          </button>
          <button className="cit-side-close" onClick={onClose} aria-label="Close sources panel">
            <X size={14} />
          </button>
        </div>
      </div>

      <div className="cit-side-body">
        {!allCitations.length ? (
          <div className="cit-side-empty" aria-live="polite">
            <FileText size={24} aria-hidden="true" />
            <p>No citations yet</p>
            <span>Ask a question to see sources</span>
          </div>
        ) : (
          Object.entries(byDocument).map(([docId, cits]) => (
            <div key={docId} className="cit-doc-group">
              <div className="cit-doc-group-header">
                <div className="cit-doc-group-name">
                  <FileText size={14} aria-hidden="true" />
                  {cits[0].documentName}
                </div>
                <span className="cit-doc-group-count">{cits.length} refs</span>
              </div>
              {cits.map((cit) => (
                <button
                  key={cit.id}
                  className="cit-item"
                  onClick={() => onOpenDocument({ documentId: cit.documentId, page: cit.page, highlightText: cit.exactQuote, citationId: cit.id, section: cit.section })}
                  aria-label={`Open citation: ${cit.section}, page ${cit.page}`}
                >
                  <ExternalLink size={12} style={{ color: '#475569', flexShrink: 0, marginTop: '0.125rem' }} aria-hidden="true" />
                  <div style={{ minWidth: 0 }}>
                    <p className="cit-item-section">{cit.section}</p>
                    <p className="cit-item-page">Page {cit.page}</p>
                    <p className="cit-item-quote">"{cit.exactQuote}"</p>
                  </div>
                </button>
              ))}
            </div>
          ))
        )}
      </div>
    </aside>
  );
}
