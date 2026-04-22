import { PersonaBO as Persona } from '@/types/persona/PersonaBO.ts';

export const personas: Persona[] = [
  {
    id: 'buy-side-equity',
    name: 'Buy-Side Equity Analyst',
    shortName: 'Buy-Side',
    icon: 'TrendingUp',
    description: 'Traditional asset manager focused on equity investments',
    suggestedQuestions: [
      'Did the company beat revenue and EPS estimates? By how much?',
      'What did management say about Q1 guidance?',
      'What are the top 3 risks mentioned in the 10-K?',
      'Calculate the current P/E ratio and compare to 5-year average',
      'What is the free cash flow yield?',
      'Summarize the competitive positioning and market share trends',
    ],
  },
  {
    id: 'sell-side-equity',
    name: 'Sell-Side Equity Analyst',
    shortName: 'Sell-Side',
    icon: 'LineChart',
    description: 'Research analyst covering the company for institutional clients',
    suggestedQuestions: [
      'What changed in the business outlook from last quarter?',
      'Summarize management\'s tone on the earnings call',
      'What questions did analysts ask about margins?',
      'Compare actual results to my published estimates: Revenue $500M, EPS $2.50',
    ],
  },
  {
    id: 'credit',
    name: 'Credit Analyst',
    shortName: 'Credit',
    icon: 'Shield',
    description: 'Fixed income analyst assessing creditworthiness',
    suggestedQuestions: [
      'What is the Total Debt/EBITDA ratio and how much covenant headroom exists?',
      'Calculate Debt Service Coverage Ratio',
      'When do the company\'s debt maturities come due?',
      'Are there any restrictive covenants limiting dividend payments?',
    ],
  },
  {
    id: 'dcm',
    name: 'DCM Analyst',
    shortName: 'DCM',
    icon: 'Building2',
    description: 'Debt capital markets analyst structuring new issuances',
    suggestedQuestions: [
      'What is the current capital structure and debt maturity profile?',
      'Calculate pro forma leverage if we issue $500M of new bonds',
      'What covenants exist in the existing credit agreement?',
      'What are the current credit spreads and how do they compare to peers?',
    ],
  },
  {
    id: 'private-markets',
    name: 'Private Markets Analyst',
    shortName: 'Private',
    icon: 'Landmark',
    description: 'PE/PC analyst evaluating private investment opportunities',
    suggestedQuestions: [
      'What is normalized EBITDA after removing owner compensation?',
      'Who are the top 10 customers and what % of revenue do they represent?',
      'Calculate LTM revenue growth and EBITDA margin',
      'What key person risks are mentioned in management discussions?',
    ],
  },
];
