import { usePersonaStore } from '@/store/personaStore';
import { Plus, FileText, ArrowRight, Calendar, CheckCircle2, Clock } from 'lucide-react';

function formatRelativeDate(isoDate: string): string {
  const diff = Date.now() - new Date(isoDate).getTime();
  const days = Math.floor(diff / 86400000);
  if (days <= 0) return 'Today';
  if (days === 1) return 'Yesterday';
  if (days < 30) return `${days} days ago`;
  return new Date(isoDate).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

export function LandingPage() {
  const activePersona = usePersonaStore((s) => s.activePersona);
  const allAnalyses = usePersonaStore((s) => s.pastAnalyses);
  const startNewAnalysis = usePersonaStore((s) => s.startNewAnalysis);
  const loadPastAnalysis = usePersonaStore((s) => s.loadPastAnalysis);

  const pastAnalyses = allAnalyses.filter((a) => a.personaId === activePersona.id);

  return (
    <div className="flex-1 overflow-y-auto px-8 py-8">
      <div className="mx-auto w-full max-w-5xl">
        {/* Header row: title left, CTA right */}
        <div className="mb-6 flex items-end justify-between">
          <div>
            <h1 className="text-xl font-bold text-white mb-1">
              {activePersona.name}
            </h1>
            <p className="text-sm text-slate-400">
              Select a past analysis or start a new one
            </p>
          </div>
          <button
            onClick={startNewAnalysis}
            className="flex items-center gap-2 rounded-xl bg-[#145D70] px-5 py-2.5 text-sm font-medium text-white transition-all hover:bg-[#1A7A92]"
          >
            <Plus className="h-4 w-4 stroke-[1.5]" />
            Start New Analysis
          </button>
        </div>

        {/* Table */}
        <div className="rounded-xl border border-[#282332] bg-[#150f1f] overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-[#282332]">
                <th className="px-5 py-3.5 text-left text-[11px] font-medium uppercase tracking-wider text-slate-500">
                  Company
                </th>
                <th className="px-5 py-3.5 text-left text-[11px] font-medium uppercase tracking-wider text-slate-500">
                  Sector
                </th>
                <th className="px-5 py-3.5 text-left text-[11px] font-medium uppercase tracking-wider text-slate-500">
                  Documents
                </th>
                <th className="px-5 py-3.5 text-left text-[11px] font-medium uppercase tracking-wider text-slate-500">
                  Status
                </th>
                <th className="px-5 py-3.5 text-left text-[11px] font-medium uppercase tracking-wider text-slate-500">
                  Date Analyzed
                </th>
                <th className="px-5 py-3.5 text-center text-[11px] font-medium uppercase tracking-wider text-slate-500">
                  Action
                </th>
              </tr>
            </thead>
            <tbody>
              {pastAnalyses.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-5 py-12 text-center text-sm text-slate-500">
                    No analyses yet. Start your first one!
                  </td>
                </tr>
              ) : (
                pastAnalyses.map((analysis) => (
                  <tr
                    key={analysis.id}
                    onClick={() => loadPastAnalysis(analysis.id)}
                    className="border-b border-[#282332]/60 last:border-b-0 cursor-pointer transition-colors hover:bg-slate-800/30"
                  >
                    <td className="px-5 py-3.5">
                      <span className="text-sm font-medium text-slate-200">
                        {analysis.companyName}
                      </span>
                    </td>
                    <td className="px-5 py-3.5">
                      <span className="text-xs text-slate-400">
                        {analysis.sector}
                      </span>
                    </td>
                    <td className="px-5 py-3.5">
                      <div className="flex items-center gap-1.5">
                        <FileText className="h-3.5 w-3.5 text-slate-500 stroke-[1.5]" />
                        <span className="text-xs text-slate-400">
                          {analysis.documentCount}
                        </span>
                      </div>
                    </td>
                    <td className="px-5 py-3.5">
                      {analysis.status === 'completed' ? (
                        <div className="flex items-center gap-1.5">
                          <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500 stroke-[1.5]" />
                          <span className="text-xs text-emerald-400">Completed</span>
                        </div>
                      ) : (
                        <div className="flex items-center gap-1.5">
                          <Clock className="h-3.5 w-3.5 text-amber-500 stroke-[1.5]" />
                          <span className="text-xs text-amber-400">In Progress</span>
                        </div>
                      )}
                    </td>
                    <td className="px-5 py-3.5">
                      <div className="flex items-center gap-1.5">
                        <Calendar className="h-3.5 w-3.5 text-slate-500 stroke-[1.5]" />
                        <span className="text-xs text-slate-400">
                          {formatRelativeDate(analysis.analyzedAt)}
                        </span>
                      </div>
                    </td>
                    <td className="px-5 py-3.5 text-center">
                      <ArrowRight className="inline-block h-4 w-4 text-slate-500 stroke-[1.5]" />
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
