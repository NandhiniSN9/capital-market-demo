import { useEffect, useState, useCallback, useRef } from 'react';
import { X, ChevronLeft, ChevronRight, FileText, Quote, Download, Loader2 } from 'lucide-react';
import { chatListService } from '@/services/chatservice/chatListServiceSelector';
import { ApiDocumentBO } from '@/types/document/ApiDocumentBO';
import { toast } from 'sonner';
import secureStorage from 'react-secure-storage';
import { SECURE_STORAGE_KEYS } from '@/helpers/storage/secureStorageKeys';
import * as pdfjsLib from 'pdfjs-dist';
import './CitationDocumentPanel.css';

pdfjsLib.GlobalWorkerOptions.workerSrc = new URL(
  'pdfjs-dist/build/pdf.worker.min.mjs',
  import.meta.url
).toString();

interface DocumentViewerState {
  isOpen: boolean;
  documentId: string | null;
  documentName: string | null;
  documentUrl: string | null;
  page: number;
  highlightText: string | null;
  citationId: string | null;
  section: string | null;
}

interface CitationDocumentPanelProps {
  documentViewer: DocumentViewerState;
  documents: ApiDocumentBO[];
  onClose: () => void;
  onNavigate: (opts: {
    documentId: string;
    page: number;
    highlightText?: string;
    citationId?: string;
    section?: string;
    documentName?: string;
    documentUrl?: string;
  }) => void;
}

interface PdfTextItem {
  str: string;
  transform: number[];
  width: number;
  height: number;
}

export function CitationDocumentPanel({
  documentViewer,
  documents,
  onClose,
  onNavigate,
}: CitationDocumentPanelProps) {
  const [pdfDoc, setPdfDoc] = useState<pdfjsLib.PDFDocumentProxy | null>(null);
  const [loading, setLoading] = useState(false);
  const [rendering, setRendering] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [renderKey, setRenderKey] = useState(0);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const highlightLayerRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const doc = documents.find((d) => d.documentId === documentViewer.documentId);
  const docName = documentViewer.documentName || doc?.fileName || 'Document';
  const pageCount = pdfDoc?.numPages || doc?.pageCount || null;

  // Load PDF when documentId changes
  const loadPdf = useCallback(async () => {
    if (!documentViewer.documentId) return;
    setLoading(true);
    setError(null);
    try {
      const chatId = secureStorage.getItem(SECURE_STORAGE_KEYS.ACTIVE_CHAT_ID) as string | null;
      if (!chatId) {
        setError('No active chat');
        setLoading(false);
        return;
      }
      const blob = await chatListService.getDocumentFile(chatId, documentViewer.documentId, 'view');
      const arrayBuffer = await blob.arrayBuffer();
      const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
      setPdfDoc(pdf);
    } catch {
      setError('Failed to load document');
    } finally {
      setLoading(false);
    }
  }, [documentViewer.documentId]);

  useEffect(() => {
    loadPdf();
    return () => {
      pdfDoc?.destroy();
    };
  }, [documentViewer.documentId]);

  // Render page with highlights
  const renderPage = useCallback(async () => {
    if (!pdfDoc || !canvasRef.current || !containerRef.current) return;
    setRendering(true);
    try {
      const pdfPage = await pdfDoc.getPage(documentViewer.page);
      const containerWidth = containerRef.current.clientWidth;
      const unscaledViewport = pdfPage.getViewport({ scale: 1 });
      const scale = containerWidth / unscaledViewport.width;
      const viewport = pdfPage.getViewport({ scale });

      const canvas = canvasRef.current;
      const ctx = canvas.getContext('2d')!;
      canvas.width = viewport.width;
      canvas.height = viewport.height;
      canvas.style.width = `${viewport.width}px`;
      canvas.style.height = `${viewport.height}px`;

      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      await pdfPage.render({ canvasContext: ctx, viewport, canvas } as any).promise;

      // Clear any previous highlights
      if (highlightLayerRef.current) {
        highlightLayerRef.current.innerHTML = '';
      }

      // Highlight text — only when highlightText is present (cleared on page nav)
      if (documentViewer.highlightText && highlightLayerRef.current) {
        const hl = highlightLayerRef.current;
        hl.innerHTML = '';
        hl.style.width = `${viewport.width}px`;
        hl.style.height = `${viewport.height}px`;

        const textContent = await pdfPage.getTextContent();
        const items = (textContent.items as PdfTextItem[]).filter((i) => i.str && i.str.trim().length > 0);

        // Extract search keywords: take distinct words (3+ chars) from the citation
        const normalize = (s: string) => s.replace(/\s+/g, ' ').trim().toLowerCase();
        const citationNorm = normalize(documentViewer.highlightText);
        // Split into words, keep meaningful ones (3+ chars, not just numbers/symbols)
        const allWords = citationNorm.split(' ').filter((w) => w.length >= 3);
        // Use first 8 words as search terms for a LIKE match
        const searchWords = allWords.slice(0, 8);

        if (searchWords.length > 0) {
          // Also try full phrase match on joined text
          const fullText = normalize(items.map((i) => i.str).join(' '));
          // Try to find the phrase (first 40 chars) in the full text
          const phraseSearch = citationNorm.slice(0, 40);
          const phraseStart = fullText.indexOf(phraseSearch);

          let matchedItemIndices = new Set<number>();

          if (phraseStart !== -1) {
            // Phrase found — highlight items that overlap with the match range
            let charCount = 0;
            const phraseEnd = phraseStart + phraseSearch.length;
            for (let idx = 0; idx < items.length; idx++) {
              const normStr = normalize(items[idx].str);
              const itemEnd = charCount + normStr.length;
              if (itemEnd > phraseStart && charCount < phraseEnd) {
                matchedItemIndices.add(idx);
              }
              charCount = itemEnd + 1;
            }
          } else {
            // Fallback: LIKE search — highlight items containing any of the search words
            for (let idx = 0; idx < items.length; idx++) {
              const itemLower = items[idx].str.toLowerCase();
              const wordHits = searchWords.filter((w) => itemLower.includes(w)).length;
              // Require at least 2 word matches per item, or 1 if the word is long (6+ chars)
              if (wordHits >= 2 || (wordHits >= 1 && searchWords.some((w) => w.length >= 6 && itemLower.includes(w)))) {
                matchedItemIndices.add(idx);
              }
            }
          }

          // Draw highlights
          for (const idx of matchedItemIndices) {
            const item = items[idx];
            const tx = item.transform[4] * scale;
            const ty = viewport.height - item.transform[5] * scale - item.height * scale;
            const w = item.width * scale;
            const h = item.height * scale * 1.3;
            const mark = document.createElement('div');
            mark.className = 'cit-doc-highlight-mark';
            mark.style.left = `${tx}px`;
            mark.style.top = `${ty}px`;
            mark.style.width = `${w}px`;
            mark.style.height = `${h}px`;
            hl.appendChild(mark);
          }

          const first = hl.querySelector('.cit-doc-highlight-mark');
          if (first) {
            setTimeout(() => first.scrollIntoView({ behavior: 'smooth', block: 'center' }), 100);
          }
        }
      }
    } catch {
      // ignore render errors
    } finally {
      setRendering(false);
    }
  }, [pdfDoc, documentViewer.page, documentViewer.highlightText]);

  useEffect(() => {
    if (pdfDoc) renderPage();
  }, [pdfDoc, documentViewer.page, documentViewer.highlightText, renderKey]);

  useEffect(() => {
    setRenderKey((k) => k + 1);
  }, [documentViewer.page, documentViewer.citationId, documentViewer.highlightText]);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [onClose]);

  const handlePrevPage = () => {
    if (documentViewer.page > 1) {
      onNavigate({
        documentId: documentViewer.documentId!,
        page: documentViewer.page - 1,
        documentName: docName,
      });
    }
  };

  const handleNextPage = () => {
    if (pageCount && documentViewer.page < pageCount) {
      onNavigate({
        documentId: documentViewer.documentId!,
        page: documentViewer.page + 1,
        documentName: docName,
      });
    }
  };

  const handleDownload = async () => {
    if (!documentViewer.documentId) return;
    try {
      const chatId = secureStorage.getItem(SECURE_STORAGE_KEYS.ACTIVE_CHAT_ID) as string | null;
      if (!chatId) return;
      toast.info(`Downloading ${docName}...`);
      const blob = await chatListService.getDocumentFile(chatId, documentViewer.documentId, 'download');
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = docName;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch {
      toast.error('Failed to download document');
    }
  };

  return (
    <div className="cit-doc-panel" role="complementary" aria-label="Document viewer">
      <div className="cit-doc-header">
        <div className="cit-doc-header-info">
          <FileText size={16} className="cit-doc-header-icon" aria-hidden="true" />
          <div className="cit-doc-header-text">
            <p className="cit-doc-title">{docName}</p>
            <p className="cit-doc-meta">
              {doc?.fileType?.toUpperCase() || 'PDF'}
              {pageCount && <> &middot; {pageCount} pages</>}
            </p>
          </div>
        </div>
        <div className="cit-doc-header-actions">
          <button className="cit-doc-btn" onClick={handleDownload} aria-label="Download document" title="Download">
            <Download size={14} aria-hidden="true" />
          </button>
          <button className="cit-doc-btn" onClick={onClose} aria-label="Close document viewer">
            <X size={16} />
          </button>
        </div>
      </div>

      {documentViewer.highlightText && (
        <div className="cit-doc-ref-card">
          <Quote size={14} className="cit-doc-ref-icon" aria-hidden="true" />
          <div className="cit-doc-ref-body">
            <p className="cit-doc-ref-label">Referenced Text</p>
            <p className="cit-doc-ref-quote">&quot;{documentViewer.highlightText}&quot;</p>
            {documentViewer.section && (
              <p className="cit-doc-ref-meta">
                Section: {documentViewer.section} &middot; Page {documentViewer.page}
              </p>
            )}
          </div>
        </div>
      )}

      <nav className="cit-doc-nav" aria-label="Page navigation">
        <button className="cit-doc-nav-btn" onClick={handlePrevPage} disabled={documentViewer.page <= 1} aria-label="Previous page">
          <ChevronLeft size={12} aria-hidden="true" /> Previous
        </button>
        <span className="cit-doc-page-info">
          Page <span className="cit-doc-page-num">{documentViewer.page}</span>
          {pageCount && <> of <span className="cit-doc-page-num">{pageCount}</span></>}
        </span>
        <button className="cit-doc-nav-btn" onClick={handleNextPage} disabled={!pageCount || documentViewer.page >= pageCount} aria-label="Next page">
          Next <ChevronRight size={12} aria-hidden="true" />
        </button>
      </nav>

      <div className="cit-doc-viewer-body" ref={containerRef}>
        {(loading || rendering) && (
          <div className="cit-doc-loading">
            <Loader2 size={24} className="animate-spin" style={{ color: '#2BB5D4' }} aria-hidden="true" />
            <p>{loading ? 'Loading document...' : 'Rendering page...'}</p>
          </div>
        )}
        {error && (
          <div className="cit-doc-error">
            <FileText size={32} style={{ color: '#475569' }} aria-hidden="true" />
            <p>{error}</p>
          </div>
        )}
        {pdfDoc && !loading && !error && (
          <div className="cit-doc-canvas-wrap">
            <canvas ref={canvasRef} className="cit-doc-canvas" />
            <div ref={highlightLayerRef} className="cit-doc-highlight-layer" />
          </div>
        )}
      </div>
    </div>
  );
}
