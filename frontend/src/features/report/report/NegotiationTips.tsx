import { ReportBlock } from '../../../design-system/report';
import { fmtCurrency } from '../../../lib/format';
import type { ValuationResult } from '../../../types';

export function NegotiationTips({ result }: { result: ValuationResult }) {
  const v = result.valuation;
  const intel = v.negotiation_intelligence;
  return (
    <ReportBlock eyebrow="Observações de negociação" title="Como defender o valor">
      <div className="mcv-negotiation-notes">
        {v.recommended_listing_price ? <p>Preço inicial recomendado: {fmtCurrency(v.recommended_listing_price)}. Faixa segura: {fmtCurrency(v.safe_price_range?.[0] || v.negotiation_floor || v.quick_sale_price)} a {fmtCurrency(v.safe_price_range?.[1] || v.negotiation_ceiling || v.market_reference)}.</p> : null}
        {intel?.quick_sale_price ? <p>Venda rápida: {fmtCurrency(intel.quick_sale_price)}. Teto provável: {fmtCurrency(v.probable_ceiling || intel.negotiation_ceiling || v.negotiation_ceiling || v.market_reference)}.</p> : null}
        {v.overvaluation_risk ? <p>Risco de supervalorização: {v.overvaluation_risk}/100. Recomendação: {v.recommended_adjustment || 'acompanhar resposta do mercado'}.</p> : null}
        {v.regional_explanation ? <p>{v.regional_explanation}</p> : null}
        {v.confidence_reason ? <p>{v.confidence_reason}</p> : null}
        {v.estimated_negotiation_margin ? <p>Margem provável de negociação: {v.estimated_negotiation_margin}% entre piso e teto da faixa.</p> : null}
        {v.market_position_percentile ? <p>Posicionamento competitivo: o valor indicado fica acima de {v.market_position_percentile}% dos anúncios comparáveis; pressão de preço {v.pricing_pressure || 'em análise'}.</p> : null}
        {v.trend_direction ? <p>Tendência de mercado: {v.trend_direction}. Use essa leitura para ajustar urgência e ancoragem.</p> : null}
        {result.insights.strengths.slice(0, 2).map((item) => <p key={item}>{item}</p>)}
      </div>
    </ReportBlock>
  );
}
