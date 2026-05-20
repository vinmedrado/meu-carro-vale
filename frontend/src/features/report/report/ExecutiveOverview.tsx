import { ReportBlock } from '../../../design-system/report';
import type { ValuationResult } from '../../../types';

export function ExecutiveOverview({ result }: { result: ValuationResult }) {
  const insight = result.valuation.executive_market_insight_v2 || result.valuation.executive_market_insight || result.insights.summary;
  const bullets = result.valuation.market_insight_bullets || [];
  const buyer = result.valuation.buyer_behavior_insights || [];
  return (
    <ReportBlock eyebrow="Resumo executivo" title="Leitura consultiva de mercado">
      <div className="mcv-executive-copy">
        <p>{insight}</p>
        <p>{result.insights.pricing_recommendation}</p>
        {bullets.length ? <ul className="mcv-methodology-list">{bullets.slice(0, 3).map((item) => <li key={item}>{item}</li>)}</ul> : null}
        {buyer.length ? <p>{buyer[0]}</p> : null}
      </div>
    </ReportBlock>
  );
}
