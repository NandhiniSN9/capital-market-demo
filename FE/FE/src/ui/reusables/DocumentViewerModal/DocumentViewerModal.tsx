import { useEffect, useRef } from 'react';
import { X, ChevronLeft, ChevronRight, FileText, Quote, Download } from 'lucide-react';
import { DocumentBO } from '../../../types/document/DocumentBO.ts';
import { toast } from 'sonner';
import './DocumentViewerModal.css';

interface DocumentViewerState {
  isOpen: boolean;
  documentId: string | null;
  page: number;
  highlightText: string | null;
  citationId: string | null;
  section: string | null;
}

interface DocumentViewerModalProps {
  documentViewer: DocumentViewerState;
  documents: DocumentBO[];
  onClose: () => void;
  onOpenDocument: (opts: { documentId: string; page: number; highlightText?: string; citationId?: string; section?: string }) => void;
}

export function DocumentViewerModal({ documentViewer, documents, onClose, onOpenDocument }: DocumentViewerModalProps) {
  const closeRef = useRef<HTMLButtonElement>(null);
  const doc = documents.find((d) => d.id === documentViewer.documentId);

  // Focus close button on open, restore on close
  useEffect(() => {
    closeRef.current?.focus();
  }, []);

  // Escape key closes
  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [onClose]);

  if (!doc) return null;

  const currentSection = doc.sections.find(
    (s) => documentViewer.page >= s.pageStart && documentViewer.page <= s.pageEnd
  );

  const handleExport = () => {
    const sectionsHtml = doc.sections.map((s) => {
      const isCurrent = currentSection?.id === s.id;
      return `<div style="margin-bottom:20px;padding:20px;border:1px solid ${isCurrent ? '#0ea5e9' : '#334155'};border-radius:8px;background:${isCurrent ? '#0c1929' : '#0f172a'};"><h3 style="color:#e2e8f0;font-size:15px;font-weight:600;margin:0 0 4px;">${s.title}</h3><p style="color:#64748b;font-size:10px;margin:0 0 12px;">Pages ${s.pageStart}–${s.pageEnd}</p><p style="color:#94a3b8;font-size:13px;line-height:1.7;margin:0;">${s.content}</p></div>`;
    }).join('');
    const citBlock = documentViewer.highlightText
      ? `<div style="margin-bottom:24px;padding:16px;border:1px solid rgba(14,165,233,0.2);border-radius:8px;background:rgba(14,165,233,0.05);"><p style="color:#38bdf8;font-size:10px;font-weight:600;text-transform:uppercase;margin:0 0 6px;">Referenced Text</p><p style="color:#cbd5e1;font-size:13px;font-style:italic;line-height:1.6;margin:0;">"${documentViewer.highlightText}"</p></div>` : '';
    const html = `<!DOCTYPE html><html><head><title>${doc.name}</title><style>body{font-family:system-ui;background:#020617;padding:32px;max-width:800px;margin:0 auto;}h1{color:#38bdf8;font-size:18px;}p.meta{color:#64748b;font-size:11px;margin-bottom:20px;}</style></head><body><h1>${doc.name}</h1><p class="meta">${doc.subType} · ${doc.period} · ${doc.pageCount} pages</p>${citBlock}${sectionsHtml}</body></html>`;
    const w = window.open('', '_blank');
    if (w) { w.document.write(html); w.document.close(); setTimeout(() => w.print(), 500); }
    toast.success('PDF export opened');
  };

  return (
    <div
      className="doc-viewer-backdrop"
      role="dialog"
      aria-modal="true"
      aria-label={`Document viewer: ${doc.name}`}
    >
      {/* Backdrop click closes */}
      <div
        style={{ position: 'absolute', inset: 0 }}
        onClick={onClose}
        aria-hidden="true"
      />

      <div className="doc-viewer-panel">
        {/* Header */}
        <div className="doc-viewer-header">
          <div className="doc-viewer-header-left">
            <FileText size={16} style={{ color: '#38bdf8' }} aria-hidden="true" />
            <div>
              <p className="doc-viewer-title">{doc.name}</p>
              <p className="doc-viewer-meta">{doc.subType} · {doc.period} · {doc.pageCount} pages</p>
            </div>
          </div>
          <div className="doc-viewer-header-right">
            <button className="doc-viewer-btn" onClick={handleExport} aria-label="Export document as PDF">
              <Download size={14} aria-hidden="true" />
              PDF
            </button>
            <button ref={closeRef} className="doc-viewer-btn" onClick={onClose} aria-label="Close document viewer">
              <X size={16} />
            </button>
          </div>
        </div>

        {/* Citation highlight card */}
        {documentViewer.highlightText && (
          <div className="doc-viewer-citation-card">
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.5rem' }}>
              <Quote size={16} style={{ color: '#38bdf8', flexShrink: 0, marginTop: '0.125rem' }} aria-hidden="true" />
              <div>
                <p className="doc-viewer-citation-label">Referenced Text</p>
                <p className="doc-viewer-citation-quote">"{documentViewer.highlightText}"</p>
                {documentViewer.section && (
                  <p className="doc-viewer-citation-meta">Section: {documentViewer.section} · Page {documentViewer.page}</p>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Page navigation */}
        <nav className="doc-viewer-nav" aria-label="Page navigation">
          <button
            className="doc-viewer-nav-btn"
            onClick={() => documentViewer.page > 1 && onOpenDocument({ documentId: doc.id, page: documentViewer.page - 1 })}
            disabled={documentViewer.page <= 1}
            aria-label="Previous page"
          >
            <ChevronLeft size={12} aria-hidden="true" />
            Previous
          </button>
          <span className="doc-viewer-page-info">
            Page <span className="doc-viewer-page-num">{documentViewer.page}</span> of <span className="doc-viewer-page-num">{doc.pageCount}</span>
          </span>
          <button
            className="doc-viewer-nav-btn"
            onClick={() => documentViewer.page < doc.pageCount && onOpenDocument({ documentId: doc.id, page: documentViewer.page + 1 })}
            disabled={documentViewer.page >= doc.pageCount}
            aria-label="Next page"
          >
            Next
            <ChevronRight size={12} aria-hidden="true" />
          </button>
        </nav>

        {/* Content */}
        <div className="doc-viewer-body">
          {currentSection ? (
            <>
              <div className="doc-viewer-section-card">
                <h2 className="doc-viewer-section-title">{currentSection.title}</h2>
                <p className="doc-viewer-section-pages">Pages {currentSection.pageStart}–{currentSection.pageEnd}</p>
                <p className="doc-viewer-section-content">{currentSection.content}</p>
                {documentViewer.highlightText && (
                  <div className="doc-viewer-highlight">
                    <p className="doc-viewer-highlight-text">
                      <span style={{ backgroundColor: 'rgba(245,158,11,0.2)', padding: '0 2px' }}>{documentViewer.highlightText}</span>
                    </p>
                  </div>
                )}
                <p className="doc-viewer-filler">
                  The information contained in this section has been prepared in accordance with generally accepted accounting principles and reflects the company's financial position as of the reporting date.
                </p>
              </div>

              {/* Section index */}
              <div className="doc-viewer-sections-card">
                <h3 className="doc-viewer-sections-label">Document Sections</h3>
                {doc.sections.map((section) => (
                  <button
                    key={section.id}
                    className={`doc-viewer-section-btn ${section.id === currentSection.id ? 'doc-viewer-section-btn--active' : 'doc-viewer-section-btn--default'}`}
                    onClick={() => onOpenDocument({ documentId: doc.id, page: section.pageStart })}
                    aria-current={section.id === currentSection.id ? 'true' : undefined}
                  >
                    <span>{section.title}</span>
                    <span className="doc-viewer-section-btn-pages">p.{section.pageStart}–{section.pageEnd}</span>
                  </button>
                ))}
              </div>
            </>
          ) : (
            <div className="doc-viewer-empty">
              <FileText size={48} style={{ color: '#334155' }} aria-hidden="true" />
              <p>Page {documentViewer.page}</p>
              <span>Content preview not available</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
