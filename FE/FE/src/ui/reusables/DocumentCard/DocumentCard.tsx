import { FileText, CheckCircle2, Loader2, X, Eye } from 'lucide-react';
import { DocumentBO as Document } from '@/types/document/DocumentBO.ts';
import { useDocumentStore } from '@/store/documentStore';
import { useUIStore } from '@/store/uiStore';
import { cn } from '@/helpers/utilities/utils';
import { format, parseISO } from 'date-fns';

interface DocumentCardProps {
  document: Document;
  categoryColor: string;
}

export function DocumentCard({ document, categoryColor }: DocumentCardProps) {
  const removeDocument = useDocumentStore((s) => s.removeDocument);
  const openDocumentViewer = useUIStore((s) => s.openDocumentViewer);

  return (
    <div
      className={cn(
        'group relative flex items-start gap-2.5 rounded-lg border-l-2 bg-slate-900/50 p-2.5 transition-all hover:bg-slate-800/50',
        categoryColor,
        document.status === 'processing' && 'shimmer'
      )}
    >
      <div className="flex-shrink-0 mt-0.5">
        <FileText className="h-4 w-4 text-slate-500" />
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-1">
          <h4 className="text-[11px] font-medium text-slate-200 leading-tight truncate pr-1">
            {document.name}
          </h4>
          <div className="flex items-center gap-0.5 flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
            <button
              onClick={() => openDocumentViewer({ documentId: document.id, page: 1 })}
              className="rounded p-0.5 text-slate-500 hover:text-sky-400 hover:bg-slate-700/50"
              title="View document"
            >
              <Eye className="h-3 w-3" />
            </button>
            <button
              onClick={() => removeDocument(document.id)}
              className="rounded p-0.5 text-slate-500 hover:text-red-400 hover:bg-slate-700/50"
              title="Remove document"
            >
              <X className="h-3 w-3" />
            </button>
          </div>
        </div>

        <div className="mt-1 flex items-center gap-2 text-[10px] text-slate-500">
          <span className="rounded bg-slate-800 px-1.5 py-0.5 font-medium">
            {document.subType}
          </span>
          <span>{document.pageCount} pages</span>
          <span>{format(parseISO(document.uploadDate), 'MMM d, yyyy')}</span>
        </div>

        <div className="mt-1.5 flex items-center gap-1">
          {document.status === 'ready' ? (
            <span className="flex items-center gap-1 text-[10px] text-emerald-400">
              <CheckCircle2 className="h-3 w-3" />
              Ready
            </span>
          ) : (
            <span className="flex items-center gap-1 text-[10px] text-amber-400">
              <Loader2 className="h-3 w-3 animate-spin" />
              Processing
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
