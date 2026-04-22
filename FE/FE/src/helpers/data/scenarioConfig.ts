import { ScenarioTypeENUM } from '@/types/chat/ScenarioTypeENUM.ts';

export interface ScenarioDefinition {
  id: string;
  value: ScenarioTypeENUM;
  name: string;
  shortName: string;
  description: string;
  suggestedQuestions: string[];
}

// Scenarios mapped by persona ID
export const PERSONA_SCENARIOS: Record<string, ScenarioDefinition[]> = {
  'buy-side-equity': [
    {
      id: 'bs-pre-earnings',
      value: ScenarioTypeENUM.PRE_EARNINGS,
      name: 'Pre-Earnings Preparation',
      shortName: 'Pre-Earnings',
      description: 'Prepare for upcoming earnings with KPIs, consensus, and positioning analysis',
      suggestedQuestions: [
        'What are the 2-3 KPIs that will move the stock?',
        'What is consensus expecting versus my own model?',
        'What narrative are bulls focused on versus bears?',
        'Has management historically beaten, met, or missed their own guidance?',
      ],
    },
    {
      id: 'bs-earnings-day',
      value: ScenarioTypeENUM.EARNINGS_DAY,
      name: 'Earnings Print Day',
      shortName: 'Earnings Day',
      description: 'Analyze the earnings release — beat/miss, variances, guidance, and tone',
      suggestedQuestions: [
        'Did revenue and EPS beat, meet, or miss consensus?',
        'What drove the variance—organic growth, acquisitions, or FX effects?',
        'Are margins expanding or compressing, and why?',
        'Did guidance get raised, lowered, or maintained?',
      ],
    },
    {
      id: 'bs-earnings-call',
      value: ScenarioTypeENUM.EARNINGS_CALL,
      name: 'Earnings Call Analysis',
      shortName: 'Earnings Call',
      description: 'Dissect the earnings call — management emphasis, deflection, and tone',
      suggestedQuestions: [
        'Which metrics does management emphasize versus downplay?',
        'Does management deflect certain analyst questions or answer vaguely?',
        'Is there consistency between prepared remarks and the financial data?',
        'What new strategic initiatives or concerns are mentioned?',
      ],
    },
    {
      id: 'bs-post-earnings',
      value: ScenarioTypeENUM.POST_EARNINGS,
      name: 'Post-Earnings Analysis',
      shortName: 'Post-Earnings',
      description: 'Post-earnings deep dive — 10-Q review, thesis assessment, and catalyst path',
      suggestedQuestions: [
        'Does the complete 10-Q reveal anything not in the press release?',
        'Should I increase, decrease, or exit the position?',
        'Has the investment thesis strengthened or weakened?',
        'What is the catalyst path for the next quarter?',
      ],
    },
  ],
  'sell-side-equity': [
    {
      id: 'ss-pre-earnings',
      value: ScenarioTypeENUM.PRE_EARNINGS,
      name: 'Pre-Earnings Preparation',
      shortName: 'Pre-Earnings',
      description: 'Prepare for earnings with consensus, debate points, and client positioning',
      suggestedQuestions: [
        'What is consensus expecting for this quarter?',
        'What is my published estimate versus the Street consensus?',
        'What are the 2-3 key debate points clients care about most?',
        'How are my clients positioned—long, short, or neutral?',
      ],
    },
    {
      id: 'ss-earnings-day',
      value: ScenarioTypeENUM.EARNINGS_DAY,
      name: 'Earnings Print Day',
      shortName: 'Earnings Day',
      description: 'Analyze the print versus your estimate and Street consensus',
      suggestedQuestions: [
        'Did the company beat, meet, or miss my published estimate?',
        'How does this compare to Street consensus expectations?',
        'What is driving the variance—revenue, margins, or one-time items?',
        'Does this require a rating or price target change?',
      ],
    },
    {
      id: 'ss-earnings-call',
      value: ScenarioTypeENUM.EARNINGS_CALL,
      name: 'Earnings Call Analysis',
      shortName: 'Earnings Call',
      description: 'Dissect the call — questions to ask, tone, and trading catalysts',
      suggestedQuestions: [
        'What questions should I ask management on the call?',
        "Is management's tone consistent with the numbers?",
        'What did management emphasize or deflect in responses?',
        'What will generate trading activity from my clients?',
      ],
    },
    {
      id: 'ss-post-earnings',
      value: ScenarioTypeENUM.POST_EARNINGS,
      name: 'Post-Earnings Analysis',
      shortName: 'Post-Earnings',
      description: 'Post-earnings — rating decision, price target, thesis update',
      suggestedQuestions: [
        'Should I upgrade, downgrade, or maintain my rating?',
        'What is my revised price target based on updated assumptions?',
        'How does this quarter change my investment thesis?',
        'What are the implications for peer companies in my coverage?',
      ],
    },
  ],
  'credit': [
    {
      id: 'cr-balance-sheet',
      value: ScenarioTypeENUM.BALANCE_SHEET_ANALYSIS,
      name: 'Balance Sheet Analysis',
      shortName: 'Balance Sheet',
      description: 'Assess financial health — net worth, working capital, liquidity, and leverage',
      suggestedQuestions: [
        "Is the company's net worth strong and stable?",
        'Is working capital adequate for the level of credit requested?',
        'What is the current ratio (Current Assets / Current Liabilities)?',
        'How much debt exists relative to equity?',
      ],
    },
    {
      id: 'cr-income-statement',
      value: ScenarioTypeENUM.INCOME_STATEMENT_ANALYSIS,
      name: 'Income Statement Analysis',
      shortName: 'Income Statement',
      description: 'Evaluate revenue trends, margins, profitability, and industry benchmarks',
      suggestedQuestions: [
        'Are revenues growing, stable, or declining?',
        'What is driving revenue changes—volume, pricing, or mix?',
        'Are gross margins improving or compressing?',
        'Is the company profitable on a sustainable basis?',
      ],
    },
    {
      id: 'cr-cash-flow',
      value: ScenarioTypeENUM.CASH_FLOW_ANALYSIS,
      name: 'Cash Flow Statement Analysis',
      shortName: 'Cash Flow',
      description: 'Analyze operating cash flow, debt service capacity, and free cash flow trends',
      suggestedQuestions: [
        'Is the company generating positive operating cash flow consistently?',
        'Is cash flow sufficient to cover debt service obligations?',
        'What is free cash flow after capex and debt service?',
        'Can the company meet covenant requirements based on projected cash flow?',
      ],
    },
    {
      id: 'cr-covenant',
      value: ScenarioTypeENUM.COVENANT_ANALYSIS,
      name: 'Covenant Analysis',
      shortName: 'Covenants',
      description: 'Review covenant definitions, headroom, default triggers, and breach risk',
      suggestedQuestions: [
        'What are the specific covenant definitions in this credit agreement?',
        'How much headroom exists on each covenant?',
        'What triggers an event of default?',
        'Are any covenants at risk of breach in the next 12 months?',
      ],
    },
  ],
  'dcm': [
    {
      id: 'dcm-creditworthiness',
      value: ScenarioTypeENUM.ISSUER_CREDITWORTHINESS,
      name: 'Issuer Creditworthiness',
      shortName: 'Creditworthiness',
      description: 'Assess debt capacity, capital structure, credit rating, and comparable offerings',
      suggestedQuestions: [
        'How much additional debt capacity does the issuer have?',
        'What is the current debt/equity ratio and how will new issuance change it?',
        'What credit rating will the new debt likely receive?',
        'How does the issuer compare to recent comparable offerings?',
      ],
    },
    {
      id: 'dcm-debt-service',
      value: ScenarioTypeENUM.DEBT_SERVICE_CAPACITY,
      name: 'Debt Service Capacity',
      shortName: 'Debt Service',
      description: 'Evaluate EBITDA sufficiency, earnings stability, coverage, and credit spreads',
      suggestedQuestions: [
        'Is EBITDA sufficient to support additional debt service?',
        'How stable are earnings through economic cycles?',
        'What is pro forma interest coverage after the new issuance?',
        'What is the appropriate credit spread for this issuer?',
      ],
    },
    {
      id: 'dcm-refinancing',
      value: ScenarioTypeENUM.REFINANCING_RISK,
      name: 'Refinancing Risk Analysis',
      shortName: 'Refinancing',
      description: 'Analyze use of proceeds, maturities, debt service capacity, and refinancing',
      suggestedQuestions: [
        'What is the use of proceeds for the new debt?',
        'Does the issuer have maturities coming due (refinancing opportunity)?',
        'Is operating cash flow sufficient to service total pro forma debt?',
        'Is this an opportunistic refinancing to lock in lower rates?',
      ],
    },
    {
      id: 'dcm-market-terms',
      value: ScenarioTypeENUM.MARKET_TERMS_ANALYSIS,
      name: 'Market Terms Analysis',
      shortName: 'Market Terms',
      description: 'Structure the offering — maturity, yield, covenants, size, and capital structure fit',
      suggestedQuestions: [
        "What is the appropriate maturity given the issuer's debt profile?",
        'What yield will clear the market based on recent comps?',
        'What covenants do investors expect for this credit profile?',
        'What size can the market absorb without significant concessions?',
      ],
    },
  ],
  'private-markets': [
    {
      id: 'pm-exploratory',
      value: ScenarioTypeENUM.EXPLORATORY_DUE_DILIGENCE,
      name: 'Exploratory Due Diligence',
      shortName: 'Exploratory DD',
      description: 'Initial screening — thesis fit, valuation, red flags, and competitive landscape',
      suggestedQuestions: [
        "Does this fit our fund's investment thesis and sector focus?",
        'Is the company size within our check range?',
        'Does the valuation make sense preliminarily?',
        'Are there obvious red flags or deal-breakers?',
      ],
    },
    {
      id: 'pm-confirmatory',
      value: ScenarioTypeENUM.CONFIRMATORY_DUE_DILIGENCE,
      name: 'Confirmatory Due Diligence',
      shortName: 'Confirmatory DD',
      description: 'Deep financial analysis — normalized EBITDA, QoE, revenue quality, and debt capacity',
      suggestedQuestions: [
        'What is normalized, sustainable EBITDA?',
        'Are there hidden liabilities or off-balance sheet items?',
        'Is revenue truly recurring or at risk of churn?',
        'How much debt can the business support?',
      ],
    },
  ],
};

export function getScenariosForPersona(personaId: string): ScenarioDefinition[] {
  return PERSONA_SCENARIOS[personaId] || [];
}

export function getScenarioById(personaId: string, scenarioId: string): ScenarioDefinition | undefined {
  const scenarios = getScenariosForPersona(personaId);
  return scenarios.find((s) => s.id === scenarioId);
}
