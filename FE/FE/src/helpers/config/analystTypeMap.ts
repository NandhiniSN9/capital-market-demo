import { AnalystTypeENUM } from '../../types/chat/AnalystTypeENUM.ts';

/**
 * Maps persona IDs used in the UI to API analyst_type values.
 */
export const PERSONA_TO_ANALYST_TYPE: Record<string, AnalystTypeENUM> = {
  'buy-side-equity': AnalystTypeENUM.BUY_SIDE,
  'sell-side-equity': AnalystTypeENUM.SELL_SIDE,
  'credit': AnalystTypeENUM.CREDIT,
  'dcm': AnalystTypeENUM.DCM,
  'private-markets': AnalystTypeENUM.PRIVATE_MARKETS,
};
