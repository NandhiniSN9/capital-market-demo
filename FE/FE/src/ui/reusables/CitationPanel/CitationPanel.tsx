import { BookOpen, FileText, ExternalLink, Download } from 'lucide-react';
import { useChatStore } from '@/store/chatStore';
import { useUIStore } from '@/store/uiStore';
import { CitationBO as CitationType } from '@/types/chat/ChatBO.ts';
import { toast } from 'sonner';

export function CitationPanel() {
  const messages = useChatStore((s) => s.messages);
  const openDocumentViewer = useUIStore((s) => s.openDocumentViewer);

  // Collect all citations from all messages
  const allCitations: CitationType[] = [];
  messages.forEach((m) => {
    if (m.citations) {
      m.citations.forEach((c) => {
        if (!allCitations.find((ac) => ac.id === c.id)) {
          allCitations.push(c);
        }
      });
    }
  });

  // Group by document
  const byDocument = allCitations.reduce<Record<string, CitationType[]>>((acc, cit) => {
    if (!acc[cit.documentId]) acc[cit.documentId] = [];
    acc[cit.documentId].push(cit);
    return acc;
  }, {});

  const handleExportPDF = () => {
    if (allCitations.length === 0) {
      toast.error('No citations to export');
      return;
    }

    const citationsByDoc = Object.entries(byDocument)
      .map(([, citations]) => {
        const rows = citations
          .map(
            (c) =>
              `<tr>
                <td style="padding:8px 12px;border-bottom:1px solid #334155;color:#94a3b8;font-size:12px;">${c.section}</td>
                <td style="padding:8px 12px;border-bottom:1px solid #334155;color:#94a3b8;font-size:12px;text-align:center;">${c.page}</td>
                <td style="padding:8px 12px;border-bottom:1px solid #334155;color:#7d8da6;font-size:11px;font-style:italic;line-height:1.5;">"${c.exactQuote}"</td>
              </tr>`
          )
          .join('');
        return `
          <div style="margin-bottom:24px;">
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
              <div style="width:6px;height:6px;border-radius:50%;background:#38bdf8;"></div>
              <h3 style="color:#e2e8f0;font-size:14px;font-weight:600;margin:0;">${citations[0].documentName}</h3>
              <span style="color:#64748b;font-size:11px;">(${citations.length} reference${citations.length > 1 ? 's' : ''})</span>
            </div>
            <table style="width:100%;border-collapse:collapse;border:1px solid #334155;border-radius:8px;overflow:hidden;">
              <thead>
                <tr style="background:#1e293b;">
                  <th style="padding:8px 12px;text-align:left;color:#64748b;font-size:11px;font-weight:500;border-bottom:1px solid #334155;">Section</th>
                  <th style="padding:8px 12px;text-align:center;color:#64748b;font-size:11px;font-weight:500;border-bottom:1px solid #334155;">Page</th>
                  <th style="padding:8px 12px;text-align:left;color:#64748b;font-size:11px;font-weight:500;border-bottom:1px solid #334155;">Quote</th>
                </tr>
              </thead>
              <tbody>${rows}</tbody>
            </table>
          </div>`;
      })
      .join('');

    const fullHTML = `<!DOCTYPE html>
      <html>
      <head>
        <title>Deal Intelligence - Sources Export</title>
        <style>
          body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #020617; padding: 32px; max-width: 900px; margin: 0 auto; }
          h1 { color: #38bdf8; font-size: 18px; margin-bottom: 4px; }
          p.sub { color: #64748b; font-size: 11px; margin-bottom: 24px; }
          @media print { body { background: #fff; } h1 { color: #0284c7; } h3 { color: #1e293b !important; } td, th { color: #334155 !important; border-color: #e2e8f0 !important; } tr { background: #fff !important; } thead tr { background: #f8fafc !important; } }
        </style>
      </head>
      <body>
        <h1>Deal Intelligence — Citation Sources</h1>
        <p class="sub">Exported on ${new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' })} · ${allCitations.length} citation${allCitations.length > 1 ? 's' : ''} across ${Object.keys(byDocument).length} document${Object.keys(byDocument).length > 1 ? 's' : ''}</p>
        ${citationsByDoc}
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
    <div className="flex h-full flex-col bg-slate-950">
      <div className="flex items-center justify-between border-b border-slate-800 px-4 py-3">
        <div className="flex items-center gap-2">
          <BookOpen className="h-4 w-4 text-sky-400" />
          <h3 className="text-sm font-semibold text-slate-200">Sources</h3>
          <span className="rounded-full bg-sky-500/10 px-2 py-0.5 text-[10px] font-medium text-sky-400">
            {allCitations.length}
          </span>
        </div>
        <button
          onClick={handleExportPDF}
          disabled={allCitations.length === 0}
          className="flex items-center gap-1.5 rounded-md px-2 py-1 text-[11px] text-slate-400 hover:bg-slate-800 hover:text-slate-200 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
          title="Export sources as PDF"
        >
          <Download className="h-3.5 w-3.5" />
          PDF
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-4">
        {Object.entries(byDocument).length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-slate-600">
            <FileText className="h-6 w-6 mb-2" />
            <p className="text-xs">No citations yet</p>
            <p className="text-[10px] mt-1">Ask a question to see sources</p>
          </div>
        ) : (
          Object.entries(byDocument).map(([docId, citations]) => (
            <div key={docId} className="rounded-lg border border-slate-800 bg-slate-900/50 overflow-hidden">
              <div className="flex items-center justify-between px-3 py-2 bg-slate-800/30">
                <div className="flex items-center gap-2">
                  <FileText className="h-3.5 w-3.5 text-slate-500" />
                  <span className="text-[11px] font-medium text-slate-300">
                    {citations[0].documentName}
                  </span>
                </div>
                <span className="rounded-full bg-slate-700 px-1.5 py-0.5 text-[9px] text-slate-400">
                  {citations.length} refs
                </span>
              </div>
              <div className="divide-y divide-slate-800/50">
                {citations.map((cit) => (
                  <button
                    key={cit.id}
                    onClick={() =>
                      openDocumentViewer({
                        documentId: cit.documentId,
                        page: cit.page,
                        highlightText: cit.exactQuote,
                        citationId: cit.id,
                        section: cit.section,
                      })
                    }
                    className="flex w-full items-start gap-2 px-3 py-2 text-left hover:bg-slate-800/30 transition-colors"
                  >
                    <ExternalLink className="h-3 w-3 text-slate-600 mt-0.5 flex-shrink-0" />
                    <div className="min-w-0">
                      <p className="text-[10px] text-sky-400 font-medium">{cit.section}</p>
                      <p className="text-[10px] text-slate-500">Page {cit.page}</p>
                      <p className="text-[10px] text-slate-500 mt-0.5 line-clamp-2 italic">
                        "{cit.exactQuote}"
                      </p>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
