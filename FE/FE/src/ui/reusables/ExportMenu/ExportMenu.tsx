import { useState, useRef, useEffect } from 'react';
import { Download, Copy, FileText, Save, Share2, Check } from 'lucide-react';
import { useChatStore } from '@/store/chatStore';
import { toast } from 'sonner';

export function ExportMenu() {
  const [open, setOpen] = useState(false);
  const [copied, setCopied] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const messages = useChatStore((s) => s.messages);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    if (open) document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [open]);

  const hasMessages = messages.length > 0;

  const handleCopyResponse = () => {
    const lastAssistant = [...messages].reverse().find((m) => m.role === 'assistant');
    if (!lastAssistant) {
      toast.error('No AI response to copy');
      return;
    }
    // Strip citation tokens for clean copy
    const cleanContent = lastAssistant.content.replace(/\{\{cit:[^}]+\}\}/g, '');
    navigator.clipboard.writeText(cleanContent);
    setCopied(true);
    toast.success('Response copied to clipboard');
    setTimeout(() => setCopied(false), 2000);
    setOpen(false);
  };

  const handleExportPDF = () => {
    // Build a formatted HTML document for print/PDF
    const printContent = messages
      .map((m) => {
        if (m.role === 'user') {
          return `<div style="margin:16px 0;padding:12px 16px;background:#1e293b;border-radius:12px;text-align:right;color:#e2e8f0;font-size:14px;">${m.content}</div>`;
        }
        const cleanContent = m.content
          .replace(/\{\{cit:[^}]+\}\}/g, '')
          .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
          .replace(/\n/g, '<br/>');
        let html = `<div style="margin:16px 0;padding:16px;background:#0f172a;border:1px solid #334155;border-radius:12px;color:#cbd5e1;font-size:13px;line-height:1.7;">${cleanContent}`;
        if (m.citations && m.citations.length > 0) {
          html += `<div style="margin-top:12px;padding-top:8px;border-top:1px solid #334155;font-size:11px;color:#94a3b8;">Sources: ${m.citations.map((c) => `${c.documentName} (p.${c.page})`).join(', ')}</div>`;
        }
        html += '</div>';
        return html;
      })
      .join('');

    const fullHTML = `
      <!DOCTYPE html>
      <html>
      <head>
        <title>Deal Intelligence - Conversation Export</title>
        <style>
          body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #020617; padding: 32px; max-width: 800px; margin: 0 auto; }
          h1 { color: #38bdf8; font-size: 18px; margin-bottom: 4px; }
          p.sub { color: #64748b; font-size: 11px; margin-bottom: 24px; }
        </style>
      </head>
      <body>
        <h1>Deal Intelligence Agent</h1>
        <p class="sub">Exported on ${new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' })}</p>
        ${printContent}
      </body>
      </html>
    `;

    const printWindow = window.open('', '_blank');
    if (printWindow) {
      printWindow.document.write(fullHTML);
      printWindow.document.close();
      printWindow.focus();
      setTimeout(() => printWindow.print(), 500);
    }
    toast.success('PDF export opened in new window');
    setOpen(false);
  };

  const handleSaveConversation = () => {
    const data = {
      exportedAt: new Date().toISOString(),
      application: 'Deal Intelligence Agent',
      messages: messages.map((m) => ({
        role: m.role,
        content: m.content.replace(/\{\{cit:[^}]+\}\}/g, ''),
        timestamp: m.timestamp,
        ...(m.citations && { citations: m.citations.map((c) => ({ document: c.documentName, section: c.section, page: c.page, quote: c.exactQuote })) }),
        ...(m.confidence && { confidence: m.confidence }),
        ...(m.calculations && { calculations: m.calculations }),
        ...(m.assumptions && { assumptions: m.assumptions }),
      })),
    };

    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `deal-intelligence-${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success('Conversation saved as JSON');
    setOpen(false);
  };

  const handleShareLink = () => {
    const fakeUrl = `https://deal-intel.app/shared/${Date.now().toString(36)}`;
    navigator.clipboard.writeText(fakeUrl);
    toast.success('Share link copied to clipboard');
    setOpen(false);
  };

  return (
    <div className="relative" ref={menuRef}>
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs text-slate-400 hover:bg-slate-800 hover:text-slate-200 transition-colors"
      >
        <Download className="h-3.5 w-3.5" />
        Export
      </button>

      {open && (
        <div className="absolute right-0 top-full mt-1 w-52 rounded-lg border border-slate-700 bg-slate-900 py-1 shadow-xl shadow-black/50 z-50">
          <button
            onClick={handleCopyResponse}
            disabled={!hasMessages}
            className="flex w-full items-center gap-2.5 px-3 py-2 text-xs text-slate-300 hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            {copied ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5 text-slate-500" />}
            Copy Last Response
          </button>
          <button
            onClick={handleExportPDF}
            disabled={!hasMessages}
            className="flex w-full items-center gap-2.5 px-3 py-2 text-xs text-slate-300 hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            <FileText className="h-3.5 w-3.5 text-slate-500" />
            Export as PDF
          </button>
          <button
            onClick={handleSaveConversation}
            disabled={!hasMessages}
            className="flex w-full items-center gap-2.5 px-3 py-2 text-xs text-slate-300 hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            <Save className="h-3.5 w-3.5 text-slate-500" />
            Save Conversation
          </button>
          <div className="mx-2 my-1 border-t border-slate-800" />
          <button
            onClick={handleShareLink}
            disabled={!hasMessages}
            className="flex w-full items-center gap-2.5 px-3 py-2 text-xs text-slate-300 hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            <Share2 className="h-3.5 w-3.5 text-slate-500" />
            Copy Share Link
          </button>
        </div>
      )}
    </div>
  );
}
