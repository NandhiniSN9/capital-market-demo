import { TrendingUp, LineChart, Shield, Building2, Landmark } from 'lucide-react';
import { useRoleSelectionVM } from './RoleSelectionScreen.vm.ts';
import DotGrid from '../../reusables/DotGrid/DotGrid.tsx';
import './RoleSelectionScreen.css';

const ICON_MAP: Record<string, React.ComponentType<{ className?: string }>> = {
  TrendingUp, LineChart, Shield, Building2, Landmark,
};

const ZEB_LOGO = 'https://zeb-uxd-figma-artifacts.s3.us-east-1.amazonaws.com/images/ZEB-Logo.svg';
const DATABRICKS_LOGO = 'https://cdn.brandfetch.io/idSUrLOWbH/theme/light/logo.svg?c=1bxid64Mup7aczewSAYMX&t=1668081623507';

export function RoleSelectionScreen() {
  const { personas, handleSelectRole } = useRoleSelectionVM();

  return (
    <main className="role-selection-root">
      <DotGrid dotSize={2} gap={10} baseColor="#282332" activeColor="#ff5f46" proximity={150} shockRadius={200} shockStrength={4} />

      <div className="role-selection-content">
        <header className="role-selection-header">
          <div className="role-selection-logos" role="img" aria-label="ZEB and Databricks logos">
            <img src={ZEB_LOGO} alt="ZEB" className="h-8 object-contain" />
            <div className="role-selection-logo-divider" aria-hidden="true" />
            <img src={DATABRICKS_LOGO} alt="Databricks" className="h-7 object-contain" />
          </div>
          <h1 className="role-selection-title">Deal Intelligence</h1>
          <p className="role-selection-subtitle">Select your role to get started</p>
        </header>

        <nav aria-label="Role selection">
          <ul className="role-cards-grid" role="list">
            {personas.map((persona) => {
              const IconComponent = ICON_MAP[persona.icon] ?? TrendingUp;
              return (
                <li key={persona.id} role="listitem">
                  <button
                    className="role-card"
                    onClick={() => handleSelectRole(persona.id)}
                    aria-label={`Select role: ${persona.name} — ${persona.description}`}
                  >
                    <div className="role-card-icon-wrap" aria-hidden="true">
                      <IconComponent className="role-card-icon" />
                    </div>
                    <h2 className="role-card-title">{persona.name}</h2>
                    <p className="role-card-desc">{persona.description}</p>
                  </button>
                </li>
              );
            })}
          </ul>
        </nav>
      </div>
    </main>
  );
}
