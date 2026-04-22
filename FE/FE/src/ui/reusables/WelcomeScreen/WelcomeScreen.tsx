import { Sparkles } from 'lucide-react';
import { usePersonaStore } from '@/store/personaStore';
import { getPersonaConfig, ICON_COMPONENT_MAP, ACCENT_CLASSES } from '@/helpers/data/personaConfig';

interface WelcomeScreenProps {
  onSendQuestion?: (q: string) => void;
}

export function WelcomeScreen({ onSendQuestion }: WelcomeScreenProps) {
  const activePersona = usePersonaStore((s) => s.activePersona);
  const activeSimulation = usePersonaStore((s) => s.activeSimulation);
  const config = getPersonaConfig(activePersona.id);
  const accent = ACCENT_CLASSES[config.accentColor];
  const IconComponent = ICON_COMPONENT_MAP[activePersona.icon];

  const questions = activeSimulation
    ? activeSimulation.suggestedQuestions
    : activePersona.suggestedQuestions.slice(0, 4);

  const subtitle = activeSimulation ? activeSimulation.name : activePersona.name;

  return (
    <div className="flex h-full items-center justify-center px-8">
      <div className="max-w-xl text-center">
        {/* Welcome hero section */}
        <div className="mb-10">
          <div className={`mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-2xl border ${accent.border} bg-[#145D70]/10`}>
            <IconComponent className="h-7 w-7 text-[#ff5f46] stroke-[1.5]" />
          </div>
          <h2 className="text-3xl font-bold text-white mb-4 leading-tight">
            {activeSimulation
              ? activeSimulation.name
              : `Welcome to ${activePersona.name.replace(/\s*Analyst$/, '')} Deal Intelligence`}
          </h2>
          <p className="text-sm text-slate-400 leading-relaxed max-w-md mx-auto">
            {activeSimulation
              ? activeSimulation.description
              : config.welcomeHelpText}
          </p>
        </div>

        <div className="mb-4">
          <div className="flex items-center justify-center gap-1.5 mb-3">
            <Sparkles className="h-3.5 w-3.5 text-[#2BB5D4] stroke-[1.5]" />
            <span className="text-[11px] font-medium text-slate-400">
              Suggested for {subtitle}
            </span>
          </div>
          <div className="grid gap-2">
            {questions.map((q, i) => (
              <button
                key={i}
                onClick={() => onSendQuestion?.(q)}
                className="group rounded-lg border border-slate-800 bg-slate-900/50 px-4 py-3 text-left text-xs text-slate-300 hover:border-[#145D70]/40 hover:bg-slate-800/50 transition-all"
              >
                <span className="group-hover:text-[#8DD8EA] transition-colors">{q}</span>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
