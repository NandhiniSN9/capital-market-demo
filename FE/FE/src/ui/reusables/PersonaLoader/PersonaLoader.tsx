import { useEffect, useState } from 'react';
import { CheckCircle2, Loader2, FileText } from 'lucide-react';
import { usePersonaStore } from '@/store/personaStore';
import { useDocumentStore } from '@/store/documentStore';
import { getPersonaConfig } from '@/helpers/data/personaConfig';

type ActivityStatus = 'pending' | 'active' | 'done';

const STEP_DURATION = 2000;
const STEP_GAP = 200;

export function PersonaLoader() {
  const activePersona = usePersonaStore((s) => s.activePersona);
  const companySetup = usePersonaStore((s) => s.companySetup);
  const setAppPhase = usePersonaStore((s) => s.setAppPhase);
  const setCompanyContext = useDocumentStore((s) => s.setCompanyContext);

  const config = getPersonaConfig(activePersona.id);
  const companyName = companySetup?.name ?? 'Company';

  const activities = config.documents.map((doc, i) => ({
    label: doc,
    delay: i * (STEP_DURATION + STEP_GAP),
    duration: STEP_DURATION,
  }));

  const totalDuration =
    activities.length * (STEP_DURATION + STEP_GAP) - STEP_GAP + 400;

  const [statuses, setStatuses] = useState<ActivityStatus[]>(
    activities.map(() => 'pending')
  );

  useEffect(() => {
    const timers: ReturnType<typeof setTimeout>[] = [];

    activities.forEach((activity, i) => {
      timers.push(
        setTimeout(() => {
          setStatuses((prev) => {
            const next = [...prev];
            next[i] = 'active';
            return next;
          });
        }, activity.delay)
      );

      timers.push(
        setTimeout(() => {
          setStatuses((prev) => {
            const next = [...prev];
            next[i] = 'done';
            return next;
          });
        }, activity.delay + activity.duration)
      );
    });

    timers.push(
      setTimeout(() => {
        if (companySetup) {
          setCompanyContext(companySetup.name);
        }
        setAppPhase('ready');
      }, totalDuration)
    );

    return () => timers.forEach(clearTimeout);
  }, []);

  return (
    <div className="flex h-full items-center justify-center px-8">
      <div className="w-full max-w-md">
        {/* Header */}
        <div className="mb-8 text-center">
          <div
            className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl border border-[#145D70]/25 bg-[#145D70]/10"
          >
            <Loader2 className="h-7 w-7 text-[#2BB5D4] animate-spin stroke-[1.5]" />
          </div>
          <h2 className="text-lg font-semibold text-slate-100 mb-1">
            Processing {companyName}
          </h2>
          <p className="text-sm text-slate-400">
            Reading company filings and disclosures...
          </p>
        </div>

        {/* Activity list */}
        <div className="space-y-3">
          {activities.map((activity, i) => {
            const status = statuses[i];

            return (
              <div
                key={i}
                className={`flex items-center gap-3 rounded-lg border px-4 py-3 transition-all duration-500 ${
                  status === 'done'
                    ? 'border-emerald-500/20 bg-emerald-500/5'
                    : status === 'active'
                    ? 'border-[#145D70]/40 bg-[#145D70]/10'
                    : 'border-slate-800 bg-slate-900/30 opacity-40'
                }`}
              >
                <div
                  className={`flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-md transition-colors duration-300 ${
                    status === 'done'
                      ? 'bg-emerald-500/15'
                      : status === 'active'
                      ? 'bg-[#145D70]/20'
                      : 'bg-slate-800'
                  }`}
                >
                  {status === 'done' ? (
                    <CheckCircle2 className="h-4 w-4 text-emerald-400 stroke-[1.5]" />
                  ) : status === 'active' ? (
                    <Loader2 className="h-4 w-4 text-[#2BB5D4] animate-spin stroke-[1.5]" />
                  ) : (
                    <FileText className="h-4 w-4 text-slate-600 stroke-[1.5]" />
                  )}
                </div>

                <div className="min-w-0 flex-1">
                  <p
                    className={`text-sm leading-snug transition-colors duration-300 ${
                      status === 'done'
                        ? 'text-emerald-300'
                        : status === 'active'
                        ? 'text-[#8DD8EA]'
                        : 'text-slate-500'
                    }`}
                  >
                    {status === 'active' ? 'Reading ' : status === 'done' ? 'Read ' : ''}
                    <span className="font-medium">{activity.label}</span>
                  </p>
                </div>
              </div>
            );
          })}
        </div>

        {/* Progress bar */}
        <div className="mt-6">
          <div className="h-1 w-full overflow-hidden rounded-full bg-slate-800">
            <div
              className="h-full rounded-full transition-all"
              style={{
                background: 'linear-gradient(to right, #145D70, #2BB5D4)',
                width: `${
                  (statuses.filter((s) => s === 'done').length / activities.length) * 100
                }%`,
                transition: 'width 0.6s ease',
              }}
            />
          </div>
          <p className="mt-2 text-center text-[11px] text-slate-500">
            {statuses.filter((s) => s === 'done').length} of {activities.length} sources processed
          </p>
        </div>
      </div>
    </div>
  );
}
