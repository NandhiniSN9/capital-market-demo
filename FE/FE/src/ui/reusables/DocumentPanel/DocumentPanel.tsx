import { useState, useCallback } from 'react';
import { Search, Upload, FileText, Eye, X, CheckCircle2, Loader2, Clock, MessageSquare, Download, AlertCircle } from 'lucide-react';
import { useDropzone } from 'react-dropzone';
import { ApiDocumentBO } from '../../../types/document/ApiDocumentBO.ts';
import { SavedConversationBO } from '../../../types/chat/ChatBO.ts';
import './DocumentPanel.css';

const DOC_CATEGORY_COLORS: Record<string, { border: string; bg: string; text: string; label: string }> = {
  financial_statement: { border: '#3b82f6', bg: 'rgba(59,130,246,0.1)', text: '#60a5fa', label: 'Financial Statements' },
  legal:              { border: '#a855f7', bg: 'rgba(168,85,247,0.1)', text: '#c084fc', label: 'Legal & Corporate' },
  operational:        { border: '#10b981', bg: 'rgba(16,185,129,0.1)', text: '#34d399', label: 'Operational' },
  market:             { border: '#f59e0b', bg: 'rgba(245,158,11,0.1)', text: '#fbbf24', label: 'Market Documents' },
};

const CATEGORY_KEYS = ['financial_statement', 'legal', 'operational', 'market'] as const;

interface DocumentPanelProps {
  documents: ApiDocumentBO[];
  filterCategory: string | null;
  searchQuery: string;
  savedConversations: SavedConversationBO[];
  onSetFilter: (category: string | null) => void;
  onSetSearch: (q: string) => void;
  onRemoveDocument: (documentId: string) => void | Promise<void>;
  onUploadFile: (file: File) => void;
  onPreviewDocument: (documentId: string, fileName: string) => void;
  onDownloadDocument: (documentId: string, fileName: string) => void;
  onSelectConversation: (sessionId: string) => void;
  documentsLoading?: boolean;
}

export function DocumentPanel({
  documents, filterCategory, searchQuery, savedConversations,
  onSetFilter, onSetSearch,
  onRemoveDocument, onUploadFile, onPreviewDocument, onDownloadDocument, onSelectConversation,
  documentsLoading = false,
}: DocumentPanelProps) {
  const [showUploader, setShowUploader] = useState(false);
  const [deletingDocId, setDeletingDocId] = useState<string | null>(null);

  const handleDelete = useCallback(async (documentId: string) => {
    setDeletingDocId(documentId);
    try {
      await onRemoveDocument(documentId);
    } finally {
      setDeletingDocId(null);
    }
  }, [onRemoveDocument]);

  const getFilteredDocuments = useCallback((): ApiDocumentBO[] => {
    let filtered = documents;
    if (filterCategory) {
      filtered = filtered.filter((d) => d.documentCategory === filterCategory);
    }
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      filtered = filtered.filter((d) => d.fileName.toLowerCase().includes(q));
    }
    return filtered;
  }, [documents, filterCategory, searchQuery]);

  const filteredDocs = getFilteredDocuments();

  const grouped = CATEGORY_KEYS
    .map((cat) => ({ category: cat, colors: DOC_CATEGORY_COLORS[cat], docs: filteredDocs.filter((d) => d.documentCategory === cat) }))
    .filter((g) => g.docs.length > 0);

  const onDrop = useCallback((accepted: File[]) => {
    accepted.forEach(onUploadFile);
    setShowUploader(false);
  }, [onUploadFile]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'], 'application/vnd.openxmlformats-officedocument.presentationml.presentation': ['.pptx'], 'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'] },
  });


  const formatTimeAgo = (ts: string) => {
    const diff = Date.now() - new Date(ts).getTime();
    const m = Math.floor(diff / 60000);
    if (m < 60) return `${m}m ago`;
    const h = Math.floor(m / 60);
    if (h < 24) return `${h}h ago`;
    return `${Math.floor(h / 24)}d ago`;
  };

  const getStatusDisplay = (status: string) => {
    switch (status) {
      case 'ready':
        return (<div className="doc-card-status-ready"><CheckCircle2 size={10} aria-hidden="true" />Ready</div>);
      case 'processing':
        return (<div className="doc-card-status-processing"><Loader2 size={10} className="animate-spin" aria-hidden="true" />Processing</div>);
      case 'failed':
        return (<div className="doc-card-status-failed"><AlertCircle size={10} aria-hidden="true" />Failed</div>);
      default:
        return (<div className="doc-card-status-processing"><Clock size={10} aria-hidden="true" />Pending</div>);
    }
  };

  return (
    <div className="doc-panel">
      {/* Header */}
      <div className="doc-panel-header">
        <div className="doc-panel-header-left">
          <FileText size={16} style={{ color: '#94a3b8' }} aria-hidden="true" />
          <h2 className="doc-panel-header-title">Documents</h2>
          <span className="doc-panel-count" aria-label={`${documents.length} documents`}>{documents.length}</span>
        </div>
        <button
          className="doc-panel-upload-btn"
          onClick={() => setShowUploader(!showUploader)}
          aria-expanded={showUploader}
          aria-label="Toggle document upload"
        >
          <Upload size={12} aria-hidden="true" />
          Upload
        </button>
      </div>

      {/* Search + filters */}
      <div className="doc-panel-search-wrap">
        <div className="doc-panel-search-inner">
          <Search size={14} className="doc-panel-search-icon" aria-hidden="true" />
          <label htmlFor="doc-search" className="sr-only">Search documents</label>
          <input
            id="doc-search"
            type="search"
            placeholder="Search documents..."
            value={searchQuery}
            onChange={(e) => onSetSearch(e.target.value)}
            className="doc-panel-search-input"
          />
        </div>
        <div className="doc-panel-filters" role="group" aria-label="Filter by document category">
          <button
            className="doc-panel-filter-btn"
            style={!filterCategory ? { backgroundColor: 'rgba(14,165,233,0.2)', color: '#7dd3fc' } : { backgroundColor: 'rgba(30,41,59,0.5)', color: '#64748b' }}
            onClick={() => onSetFilter(null)}
            aria-pressed={!filterCategory}
          >
            All
          </button>
          {CATEGORY_KEYS.map((cat) => {
            const c = DOC_CATEGORY_COLORS[cat];
            return (
              <button
                key={cat}
                className="doc-panel-filter-btn"
                style={filterCategory === cat
                  ? { backgroundColor: c.bg, color: c.text }
                  : { backgroundColor: 'rgba(30,41,59,0.5)', color: '#64748b' }}
                onClick={() => onSetFilter(filterCategory === cat ? null : cat)}
                aria-pressed={filterCategory === cat}
              >
                {c.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Upload dropzone */}
      {showUploader && (
        <div className="doc-panel-upload-zone">
          <div
            {...getRootProps()}
            className={`doc-panel-dropzone ${isDragActive ? 'doc-panel-dropzone--active' : 'doc-panel-dropzone--idle'}`}
            role="button"
            aria-label="Drop files here or click to browse"
            tabIndex={0}
          >
            <input {...getInputProps()} aria-label="File upload input" />
            <Upload size={20} style={{ color: isDragActive ? '#38bdf8' : '#475569' }} aria-hidden="true" />
            <p className="doc-panel-dropzone-text">{isDragActive ? 'Drop files here' : 'Drag & drop or click to browse'}</p>
            <p className="doc-panel-dropzone-hint">PDF, PPTX, DOCX</p>
          </div>
        </div>
      )}

      {/* Document list */}
      <div className="doc-panel-list-wrap" style={{ position: 'relative', flex: 1, minHeight: '200px', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        {documentsLoading && (
          <div
            className="doc-panel-list-loading"
            aria-live="polite"
            aria-label="Refreshing documents"
            style={{
              position: 'absolute', inset: 0, zIndex: 10,
              display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
              gap: '0.5rem',
              backgroundColor: 'rgba(2, 6, 23, 0.7)',
              backdropFilter: 'blur(2px)',
            }}
          >
            <Loader2 size={20} className="animate-spin" style={{ color: '#2BB5D4' }} aria-hidden="true" />
            <p style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Refreshing documents...</p>
          </div>
        )}
        <div className="doc-panel-list" role="region" aria-label="Document list" style={{ minHeight: 0, flex: 1, overflowY: 'auto' }}>
        {grouped.length === 0 ? (
          <div className="doc-panel-empty" aria-live="polite">
            <FileText size={32} aria-hidden="true" />
            <p>No documents found</p>
          </div>
        ) : (
          grouped.map((group) => (
            <div key={group.category} className="doc-panel-group">
              <div className="doc-panel-group-header">
                <span className="doc-panel-group-label" style={{ color: group.colors.text }}>{group.colors.label}</span>
                <span className="doc-panel-group-count">({group.docs.length})</span>
              </div>
              {group.docs.map((doc) => (
                <article key={doc.documentId} className="doc-card" style={{ borderLeftColor: group.colors.border, opacity: deletingDocId === doc.documentId ? 0.5 : 1, pointerEvents: deletingDocId === doc.documentId ? 'none' : 'auto' }} aria-label={doc.fileName}>
                  {deletingDocId === doc.documentId ? (
                    <Loader2 size={16} className="animate-spin" style={{ color: '#f87171', flexShrink: 0, marginTop: '0.125rem' }} aria-hidden="true" />
                  ) : (
                    <FileText size={16} style={{ color: '#64748b', flexShrink: 0, marginTop: '0.125rem' }} aria-hidden="true" />
                  )}
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <p className="doc-card-name">{deletingDocId === doc.documentId ? `Deleting ${doc.fileName}...` : doc.fileName}</p>
                    <div className="doc-card-meta">
                      <span className="doc-card-subtype">{doc.fileType.toUpperCase()}</span>
                      {doc.pageCount !== null && <span className="doc-card-pages">{doc.pageCount}p</span>}
                      <span className="doc-card-pages">{formatTimeAgo(doc.uploadedAt)}</span>
                    </div>
                    {getStatusDisplay(doc.processingStatus)}
                  </div>
                  <div className="doc-card-actions">
                    <button
                      className="doc-card-action-btn"
                      onClick={() => onPreviewDocument(doc.documentId, doc.fileName)}
                      aria-label={`Preview ${doc.fileName}`}
                    >
                      <Eye size={12} />
                    </button>
                    <button
                      className="doc-card-action-btn"
                      onClick={() => onDownloadDocument(doc.documentId, doc.fileName)}
                      aria-label={`Download ${doc.fileName}`}
                    >
                      <Download size={12} />
                    </button>
                    <button
                      className="doc-card-action-btn doc-card-action-btn--danger"
                      onClick={() => handleDelete(doc.documentId)}
                      disabled={deletingDocId !== null}
                      aria-label={`Remove ${doc.fileName}`}
                    >
                      <X size={12} />
                    </button>
                  </div>
                </article>
              ))}
            </div>
          ))
        )}

      </div>
      </div>

      {/* Conversation history — outside the scrollable document list */}
      {savedConversations.length > 0 && (
        <div className="conv-history" style={{ flexShrink: 0, maxHeight: '200px', overflowY: 'auto' }}>
          <div className="conv-history-header">
            <Clock size={12} style={{ color: '#475569' }} aria-hidden="true" />
            <span className="conv-history-label">Recent Conversations</span>
          </div>
          {savedConversations.map((conv) => (
            <button
              key={conv.id}
              className="conv-item"
              onClick={() => onSelectConversation(conv.id)}
              aria-label={`Load conversation: ${conv.title}`}
            >
              <MessageSquare size={14} style={{ color: '#475569', flexShrink: 0, marginTop: '0.125rem' }} aria-hidden="true" />
              <div style={{ minWidth: 0, flex: 1 }}>
                <p className="conv-item-title">{conv.title}</p>
                <div className="conv-item-meta">
                  <span>{conv.messageCount} messages</span>
                  <span>·</span>
                  <span>{formatTimeAgo(conv.timestamp)}</span>
                </div>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
