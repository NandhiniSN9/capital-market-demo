import { useState } from 'react';
import { Search, Upload, FileText } from 'lucide-react';
import { useDocumentStore } from '@/store/documentStore';
import { DocumentCard } from '../DocumentCard/DocumentCard';
import { DocumentUploader } from '@/ui/reusables/DocumentUploader/DocumentUploader';
import { cn } from '@/helpers/utilities/utils';

const documentCategories = [
  { type: 'financial' as const, label: 'Financial', color: '#3b82f6', bgColor: 'bg-blue-500/10', textColor: 'text-blue-400' },
  { type: 'legal' as const, label: 'Legal', color: '#a855f7', bgColor: 'bg-purple-500/10', textColor: 'text-purple-400' },
  { type: 'operational' as const, label: 'Operational', color: '#10b981', bgColor: 'bg-emerald-500/10', textColor: 'text-emerald-400' },
  { type: 'market' as const, label: 'Market', color: '#f59e0b', bgColor: 'bg-amber-500/10', textColor: 'text-amber-400' },
];

export function DocumentLibrary() {
  const documents = useDocumentStore((s) => s.documents);
  const filterType = useDocumentStore((s) => s.filterType);
  const searchQuery = useDocumentStore((s) => s.searchQuery);
  const setFilter = useDocumentStore((s) => s.setFilter);
  const setSearch = useDocumentStore((s) => s.setSearch);
  const getFilteredDocuments = useDocumentStore((s) => s.getFilteredDocuments);
  const [showUploader, setShowUploader] = useState(false);

  const filteredDocs = getFilteredDocuments();

  const groupedDocs = documentCategories.map((cat) => ({
    ...cat,
    documents: filteredDocs.filter((d) => d.type === cat.type),
  })).filter((g) => g.documents.length > 0);

  return (
    <div className="flex flex-col h-full min-h-0">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 px-4 py-3">
        <div className="flex items-center gap-2">
          <FileText className="h-4 w-4 text-slate-400" />
          <h2 className="text-sm font-semibold text-slate-200">Documents</h2>
          <span className="rounded-full bg-slate-800 px-2 py-0.5 text-[10px] font-medium text-slate-400">
            {documents.length}
          </span>
        </div>
        <button
          onClick={() => setShowUploader(!showUploader)}
          className="flex items-center gap-1 rounded-md bg-sky-500/10 px-2 py-1 text-[11px] font-medium text-sky-400 hover:bg-sky-500/20 transition-colors"
        >
          <Upload className="h-3 w-3" />
          Upload
        </button>
      </div>

      {/* Search */}
      <div className="border-b border-slate-800/50 px-3 py-2">
        <div className="relative">
          <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-slate-500" />
          <input
            type="text"
            placeholder="Search documents..."
            value={searchQuery}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded-md bg-slate-800/50 py-1.5 pl-8 pr-3 text-xs text-slate-300 placeholder-slate-600 outline-none focus:bg-slate-800 focus:ring-1 focus:ring-sky-500/50 transition-all"
          />
        </div>

        {/* Type filters */}
        <div className="mt-2 flex gap-1 flex-wrap">
          <button
            onClick={() => setFilter(null)}
            className={cn(
              'rounded-full px-2.5 py-0.5 text-[10px] font-medium transition-colors',
              !filterType
                ? 'bg-sky-500/20 text-sky-300'
                : 'bg-slate-800/50 text-slate-500 hover:text-slate-300'
            )}
          >
            All
          </button>
          {documentCategories.map((cat) => (
            <button
              key={cat.type}
              onClick={() => setFilter(filterType === cat.type ? null : cat.type)}
              className={cn(
                'rounded-full px-2.5 py-0.5 text-[10px] font-medium transition-colors',
                filterType === cat.type
                  ? `${cat.bgColor} ${cat.textColor}`
                  : 'bg-slate-800/50 text-slate-500 hover:text-slate-300'
              )}
            >
              {cat.label}
            </button>
          ))}
        </div>
      </div>

      {/* Upload zone */}
      {showUploader && (
        <div className="border-b border-slate-800/50 p-3">
          <DocumentUploader onClose={() => setShowUploader(false)} />
        </div>
      )}

      {/* Document list */}
      <div className="flex-1 min-h-0 overflow-y-auto px-3 py-2 space-y-3">
        {groupedDocs.map((group) => (
          <div key={group.type}>
            <div className="mb-1.5 flex items-center gap-1.5">
              <span className={cn('text-[10px] font-semibold uppercase tracking-wider', group.textColor)}>
                {group.label}
              </span>
              <span className="text-[10px] text-slate-600">({group.documents.length})</span>
            </div>
            <div className="space-y-1">
              {group.documents.map((doc) => (
                <DocumentCard key={doc.id} document={doc} categoryColor={group.color} />
              ))}
            </div>
          </div>
        ))}

        {filteredDocs.length === 0 && (
          <div className="flex flex-col items-center justify-center py-12 text-slate-600">
            <FileText className="h-8 w-8 mb-2" />
            <p className="text-xs">No documents found</p>
          </div>
        )}
      </div>
    </div>
  );
}
