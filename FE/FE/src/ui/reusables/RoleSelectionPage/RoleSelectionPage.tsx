import { usePersonaStore } from '@/store/personaStore';
import { getPersonaConfig, ICON_COMPONENT_MAP, ACCENT_CLASSES } from '@/helpers/data/personaConfig';
import DotGrid from '@/ui/reusables/DotGrid/DotGrid';

const ZEB_LOGO = 'https://zeb-uxd-figma-artifacts.s3.us-east-1.amazonaws.com/images/ZEB-Logo.svg';
const DATABRICKS_LOGO = 'https://cdn.brandfetch.io/idSUrLOWbH/theme/light/logo.svg?c=1bxid64Mup7aczewSAYMX&t=1668081623507';

export function RoleSelectionPage() {
  const personas = usePersonaStore((s) => s.personas);
  const selectRole = usePersonaStore((s) => s.selectRole);

  return (
    <div className="relative flex h-full items-center justify-center px-6 py-12 overflow-hidden">
      <DotGrid dotSize={2} gap={10} baseColor="#282332" activeColor="#ff5f46" proximity={150} shockRadius={200} shockStrength={4} />
      <div className="relative z-10 w-full max-w-6xl">
        {/* Header — ZEB + Databricks logos + Hero text */}
        <div className="mb-14 text-center">
          <div className="mx-auto mb-8 flex items-center justify-center gap-4">
            <img src={ZEB_LOGO} alt="ZEB" className="h-8 object-contain" />
            <div className="h-8 w-px bg-slate-700" />
            <img src={DATABRICKS_LOGO} alt="Databricks" className="h-7 object-contain" />
          </div>
          <h1 className="text-4xl font-bold tracking-tight text-white mb-4">
            Deal Intelligence
          </h1>
          <p className="text-base text-slate-400 max-w-md mx-auto leading-relaxed">
            Select your role to get started
          </p>
        </div>

        {/* Role Cards — single row */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5">
          {personas.map((persona) => {
            const config = getPersonaConfig(persona.id);
            const accent = ACCENT_CLASSES[config.accentColor];
            const IconComponent = ICON_COMPONENT_MAP[persona.icon];

            return (
              <button
                key={persona.id}
                onClick={() => selectRole(persona.id)}
                className="group flex flex-col items-start rounded-xl border border-[#282332] bg-[#150f1f] p-5 text-left transition-all duration-200 cursor-pointer hover:border-[#145D70]/40 hover:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-[#145D70]/40 focus:ring-offset-2 focus:ring-offset-slate-950"
              >
                {/* Icon — thin line style */}
                <div className={`mb-4 flex h-11 w-11 items-center justify-center rounded-xl border ${accent.border} transition-all duration-200 group-hover:scale-105`}
                  style={{ background: 'rgba(20, 93, 112, 0.08)' }}
                >
                  <IconComponent className="h-5 w-5 text-[#ff5f46] stroke-[1.5]" />
                </div>

                {/* Title & Description */}
                <h3 className="text-sm font-semibold text-slate-100 mb-1.5 group-hover:text-white transition-colors">
                  {persona.name}
                </h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  {persona.description}
                </p>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
