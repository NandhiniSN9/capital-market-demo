import { useEffect } from 'react';
import { X, ChevronLeft, ChevronRight, FileText, Quote, Download } from 'lucide-react';
import { useUIStore } from '@/store/uiStore';
import { useDocumentStore } from '@/store/documentStore';
import { cn } from '@/helpers/utilities/utils';
import { toast } from 'sonner';

export function DocumentViewer() {
  const documentViewer = useUIStore((s) => s.documentViewer);
  const closeDocumentViewer = useUIStore((s) => s.closeDocumentViewer);
  const openDocumentViewer = useUIStore((s) => s.openDocumentViewer);
  const documents = useDocumentStore((s) => s.documents);

  const doc = documents.find((d) => d.id === documentViewer.documentId);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') closeDocumentViewer();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [closeDocumentViewer]);

  if (!doc) return null;

  const currentSection = doc.sections.find(
    (s) => documentViewer.page >= s.pageStart && documentViewer.page <= s.pageEnd
  );

  const handleExportPDF = () => {
    const sectionsHTML = doc.sections
      .map((section) => {
        const isCurrent = currentSection && section.id === currentSection.id;
        return `
          <div style="margin-bottom:20px;padding:20px;border:1px solid ${isCurrent ? '#0ea5e9' : '#334155'};border-radius:8px;background:${isCurrent ? '#0c1929' : '#0f172a'};">
            <h3 style="color:#e2e8f0;font-size:15px;font-weight:600;margin:0 0 4px 0;">${section.title}</h3>
            <p style="color:#64748b;font-size:10px;margin:0 0 12px 0;">Pages ${section.pageStart}–${section.pageEnd}</p>
            <p style="color:#94a3b8;font-size:13px;line-height:1.7;margin:0;">${section.content}</p>
          </div>`;
      })
      .join('');

    const citationBlock = documentViewer.highlightText
      ? `<div style="margin-bottom:24px;padding:16px;border:1px solid rgba(14,165,233,0.2);border-radius:8px;background:rgba(14,165,233,0.05);">
          <p style="color:#38bdf8;font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;margin:0 0 6px 0;">Referenced Text</p>
          <p style="color:#cbd5e1;font-size:13px;font-style:italic;line-height:1.6;margin:0;">"${documentViewer.highlightText}"</p>
          ${documentViewer.section ? `<p style="color:#64748b;font-size:10px;margin:8px 0 0 0;">Section: ${documentViewer.section} · Page ${documentViewer.page}</p>` : ''}
        </div>`
      : '';

    const fullHTML = `<!DOCTYPE html>
      <html>
      <head>
        <title>${doc.name} - Export</title>
        <style>
          body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #020617; padding: 32px; max-width: 800px; margin: 0 auto; }
          h1 { color: #38bdf8; font-size: 18px; margin-bottom: 2px; }
          p.meta { color: #64748b; font-size: 11px; margin-bottom: 20px; }
          @media print {
            body { background: #fff; padding: 24px; }
            h1 { color: #0284c7; }
            h3 { color: #1e293b !important; }
            p { color: #334155 !important; }
            div { border-color: #e2e8f0 !important; background: #fff !important; }
            p.meta { color: #64748b !important; }
          }
        </style>
      </head>
      <body>
        <h1>${doc.name}</h1>
        <p class="meta">${doc.subType} · ${doc.period} · ${doc.pageCount} pages · Exported on ${new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' })}</p>
        ${citationBlock}
        ${sectionsHTML}
      </body>
      </html>`;

    const printWindow = window.open('', '_blank');
    if (printWindow) {
      printWindow.document.write(fullHTML);
      printWindow.document.close();
      printWindow.focus();
      setTimeout(() => printWindow.print(), 500);
    }
    toast.success('PDF export opened in new window');
  };

  return (
    <div className="fixed inset-0 z-50 flex">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={closeDocumentViewer} />

      {/* Viewer panel */}
      <div className="relative ml-auto flex h-full w-full max-w-3xl flex-col bg-slate-900 shadow-2xl shadow-black/50 animate-in slide-in-from-right duration-300">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-700 px-4 py-3">
          <div className="flex items-center gap-3">
            <FileText className="h-4 w-4 text-sky-400" />
            <div>
              <h3 className="text-sm font-medium text-slate-100">{doc.name}</h3>
              <p className="text-[10px] text-slate-500">
                {doc.subType} &middot; {doc.period} &middot; {doc.pageCount} pages
              </p>
            </div>
          </div>
          <div className="flex items-center gap-1">
            <button
              onClick={handleExportPDF}
              className="flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-[11px] text-slate-400 hover:bg-slate-800 hover:text-slate-200 transition-colors"
              title="Export document as PDF"
            >
              <Download className="h-3.5 w-3.5" />
              PDF
            </button>
            <button
              onClick={closeDocumentViewer}
              className="rounded-md p-1.5 text-slate-400 hover:bg-slate-800 hover:text-slate-200 transition-colors"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* Citation info card (if opened from a citation) */}
        {documentViewer.highlightText && (
          <div className="mx-4 mt-3 rounded-lg border border-sky-500/20 bg-sky-500/5 p-3">
            <div className="flex items-start gap-2">
              <Quote className="h-4 w-4 text-sky-400 mt-0.5 flex-shrink-0" />
              <div>
                <p className="text-[10px] font-medium text-sky-400 uppercase tracking-wider mb-1">
                  Referenced Text
                </p>
                <p className="text-xs text-slate-300 leading-relaxed italic">
                  "{documentViewer.highlightText}"
                </p>
                {documentViewer.section && (
                  <p className="mt-1.5 text-[10px] text-slate-500">
                    Section: {documentViewer.section} &middot; Page {documentViewer.page}
                  </p>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Page navigation */}
        <div className="flex items-center justify-between border-b border-slate-800 px-4 py-2">
          <button
            onClick={() => {
              if (documentViewer.page > 1) {
                openDocumentViewer({
                  documentId: doc.id,
                  page: documentViewer.page - 1,
                });
              }
            }}
            disabled={documentViewer.page <= 1}
            className="flex items-center gap-1 rounded px-2 py-1 text-xs text-slate-400 hover:bg-slate-800 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
          >
            <ChevronLeft className="h-3 w-3" />
            Previous
          </button>
          <span className="text-xs text-slate-400">
            Page <span className="font-mono text-slate-200">{documentViewer.page}</span> of{' '}
            <span className="font-mono">{doc.pageCount}</span>
          </span>
          <button
            onClick={() => {
              if (documentViewer.page < doc.pageCount) {
                openDocumentViewer({
                  documentId: doc.id,
                  page: documentViewer.page + 1,
                });
              }
            }}
            disabled={documentViewer.page >= doc.pageCount}
            className="flex items-center gap-1 rounded px-2 py-1 text-xs text-slate-400 hover:bg-slate-800 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
          >
            Next
            <ChevronRight className="h-3 w-3" />
          </button>
        </div>

        {/* Document content (simulated) */}
        <div className="flex-1 overflow-y-auto p-6">
          {currentSection ? (
            <div className="space-y-6">
              <div className="rounded-lg border border-slate-800 bg-slate-950/50 p-6">
                <h2 className="text-lg font-semibold text-slate-100 mb-1">
                  {currentSection.title}
                </h2>
                <p className="text-[10px] text-slate-500 mb-4">
                  Pages {currentSection.pageStart}–{currentSection.pageEnd}
                </p>
                <div className="prose prose-invert prose-sm max-w-none">
                  <p className="text-sm text-slate-300 leading-relaxed">
                    {currentSection.content}
                  </p>

                  {/* Simulated additional document content */}
                  <div className="mt-6 space-y-4">
                    {documentViewer.highlightText && (
                      <div className="rounded-md bg-amber-500/10 border border-amber-500/20 p-3">
                        <p className="text-xs text-amber-200/80 leading-relaxed">
                          <span className="bg-amber-500/20 px-0.5">{documentViewer.highlightText}</span>
                        </p>
                      </div>
                    )}

                    <p className="text-sm text-slate-400 leading-relaxed">
                      The information contained in this section has been prepared in accordance
                      with generally accepted accounting principles and reflects the company's
                      financial position as of the reporting date. All figures are presented in
                      millions of U.S. dollars unless otherwise stated.
                    </p>
                    <p className="text-sm text-slate-400 leading-relaxed">
                      Forward-looking statements in this document are subject to risks and
                      uncertainties that could cause actual results to differ materially from
                      those expressed or implied. Readers should not place undue reliance on
                      any forward-looking statements.
                    </p>
                  </div>
                </div>
              </div>

              {/* Section index */}
              <div className="rounded-lg border border-slate-800 bg-slate-950/50 p-4">
                <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
                  Document Sections
                </h3>
                <div className="space-y-1">
                  {doc.sections.map((section) => (
                    <button
                      key={section.id}
                      onClick={() => {
                        openDocumentViewer({
                          documentId: doc.id,
                          page: section.pageStart,
                        });
                      }}
                      className={cn(
                        'flex w-full items-center justify-between rounded-md px-3 py-2 text-xs transition-colors',
                        section.id === currentSection.id
                          ? 'bg-sky-500/10 text-sky-300'
                          : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
                      )}
                    >
                      <span>{section.title}</span>
                      <span className="text-[10px] text-slate-600">
                        p.{section.pageStart}–{section.pageEnd}
                      </span>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="flex h-full items-center justify-center">
              <div className="text-center">
                <FileText className="h-12 w-12 text-slate-700 mx-auto mb-3" />
                <p className="text-sm text-slate-500">Page {documentViewer.page}</p>
                <p className="text-xs text-slate-600 mt-1">Content preview not available</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
