import { TrendingUp, LineChart, Shield, Building2, Landmark } from 'lucide-react';

export interface PersonaConfig {
  title: string;
  description: string;
  welcomeHelpText: string;
  accentColor: string;
  documents: string[];
  defaultCompany: string | null;
  urlPlaceholder: string;
}

// Primary brand accent: #145D70
// RGB: 20, 93, 112

export const PERSONA_CONFIGS: Record<string, PersonaConfig> = {
  'buy-side-equity': {
    title: 'Equity Investment Analysis',
    description: 'Enter the company details to begin investment analysis for your portfolio.',
    welcomeHelpText: 'Analyze earnings reports, evaluate investment theses, and extract key financial metrics from SEC filings with precise citations.',
    accentColor: 'brand',
    documents: [
      '10-K and 10-Q filings',
      'Earnings transcripts',
      'Equity research reports',
      'Financial models and projections',
    ],
    defaultCompany: null,
    urlPlaceholder: 'e.g. https://investor.apple.com',
  },
  'sell-side-equity': {
    title: 'Sell-Side Equity Analysis',
    description: 'Enter the company details to begin earnings analysis for your institutional clients.',
    welcomeHelpText: 'Rapidly analyze earnings prints, compare results to consensus estimates, and draft research notes with sourced citations for your institutional clients.',
    accentColor: 'brand',
    documents: [
      '8-K filing with earnings press release',
      'Earnings presentations',
      'Non-GAAP reconciliations & supplemental disclosures',
      'Guidance and management commentary',
    ],
    defaultCompany: null,
    urlPlaceholder: 'e.g. https://investor.apple.com',
  },
  credit: {
    title: 'Credit Analysis',
    description: 'Enter the company details to assess creditworthiness and debt capacity.',
    welcomeHelpText: 'Assess creditworthiness, calculate covenant compliance ratios, and monitor debt service capacity from credit agreements and financial filings.',
    accentColor: 'brand',
    documents: [
      'Credit agreements and loan documents',
      'Financial covenants and compliance reports',
      'Debt maturity schedules',
      'Rating agency reports and assessments',
    ],
    defaultCompany: 'Meridian Healthcare',
    urlPlaceholder: 'e.g. https://investor.apple.com',
  },
  dcm: {
    title: 'DCM Analysis',
    description: 'Enter the company details to structure and analyze debt capital markets issuances.',
    welcomeHelpText: 'Structure debt offerings, analyze capital structures, and evaluate pricing comparables from bond indentures and market data.',
    accentColor: 'brand',
    documents: [
      'Capital structure overview',
      'Bond indentures and term sheets',
      'Pricing comparables and market data',
      'Covenant packages and credit documentation',
    ],
    defaultCompany: 'Pinnacle Infrastructure Holdings',
    urlPlaceholder: 'e.g. https://investor.apple.com',
  },
  'private-markets': {
    title: 'Private Markets Analysis',
    description: 'Enter the company details to evaluate private investment opportunities.',
    welcomeHelpText: 'Analyze private market opportunities, evaluate quality of earnings, and extract insights from CIMs and due diligence materials.',
    accentColor: 'brand',
    documents: [
      'CIM / Management presentation',
      'Quality of earnings report',
      'Due diligence materials',
      'Cap table and waterfall analysis',
    ],
    defaultCompany: 'Apex Manufacturing Group',
    urlPlaceholder: 'https://stripe.com/in',
  },
};

export function getPersonaConfig(personaId: string): PersonaConfig {
  return PERSONA_CONFIGS[personaId] ?? PERSONA_CONFIGS['buy-side-equity'];
}

export const ICON_COMPONENTS = {
  TrendingUp,
  LineChart,
  Shield,
  Building2,
  Landmark,
};

export const ICON_COMPONENT_MAP: Record<string, React.ComponentType<{ className?: string }>> = {
  TrendingUp,
  LineChart,
  Shield,
  Building2,
  Landmark,
};

// Unified brand accent color: #145D70
// All personas use the same color for visual consistency
export const ACCENT_CLASSES: Record<string, {
  bg: string;
  bgStrong: string;
  border: string;
  borderStrong: string;
  text: string;
  textLight: string;
  gradient: string;
  hoverBorder: string;
  focusBorder: string;
  focusRing: string;
  dotBg: string;
  buttonBg: string;
  buttonHover: string;
  progressGradient: string;
  chipBg: string;
  chipBorder: string;
  chipText: string;
  chipSubtext: string;
  chipLinkText: string;
  chipLinkHover: string;
}> = {
  brand: {
    bg: 'bg-[#145D70]/10',
    bgStrong: 'bg-[#145D70]/20',
    border: 'border-[#145D70]/25',
    borderStrong: 'border-[#145D70]/40',
    text: 'text-[#2BB5D4]',
    textLight: 'text-[#8DD8EA]',
    gradient: 'from-[#145D70]/20 to-[#0E4150]/20',
    hoverBorder: 'hover:border-[#145D70]/40',
    focusBorder: 'focus:border-[#145D70]/60',
    focusRing: 'focus:ring-[#145D70]/20',
    dotBg: 'bg-[#145D70]/70',
    buttonBg: 'bg-[#145D70]',
    buttonHover: 'hover:bg-[#1A7A92]',
    progressGradient: 'from-[#145D70] to-[#2BB5D4]',
    chipBg: 'bg-[#145D70]/10',
    chipBorder: 'border-[#145D70]/25',
    chipText: 'text-[#8DD8EA]',
    chipSubtext: 'text-[#2BB5D4]/70',
    chipLinkText: 'text-[#2BB5D4]',
    chipLinkHover: 'hover:text-[#8DD8EA]',
  },
};
