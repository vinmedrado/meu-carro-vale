import { ValuationRange } from '../../../design-system/report';
import type { ValuationResult } from '../../../types';
import { getRecommendedTopPrice } from '../../../lib/valuationAccessors';

export function MarketRange({ result }: { result: ValuationResult }) {
  const v = result.valuation;
  return <ValuationRange quick={v.quick_sale_price} ideal={v.ideal_price} recommendedTop={getRecommendedTopPrice(v)} />;
}
