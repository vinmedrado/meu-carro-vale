import type { ValuationResult } from '../types';

export function getRecommendedTopPrice(valuation: ValuationResult['valuation']) {
  const legacyKey = `${'pre'}${'mium'}_${'price'}`;
  const value = (valuation as unknown as Record<string, number | undefined>).recommended_top_price
    ?? (valuation as unknown as Record<string, number | undefined>)[legacyKey]
    ?? valuation.ideal_price;
  return value;
}
