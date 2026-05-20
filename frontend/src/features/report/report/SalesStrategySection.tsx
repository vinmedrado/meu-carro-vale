import { ExecutiveTable, ReportBlock } from '../../../design-system/report';
import { fmtCurrency } from '../../../lib/format';
import type { ValuationResult } from '../../../types';

export function SalesStrategySection({ result }: { result: ValuationResult }) {
  const v = result.valuation;
  const decision = v.selling_decision || {};
  const listing = v.listing_price || decision.listing_price || v.recommended_listing_price || v.ideal_price;
  const closeMin = v.ideal_close_range_min || decision.ideal_close_range_min || v.safe_price_range?.[0] || v.negotiation_floor || v.quick_sale_price;
  const closeMax = v.ideal_close_range_max || decision.ideal_close_range_max || v.safe_price_range?.[1] || v.negotiation_ceiling || v.ideal_price;
  const minimum = v.minimum_recommended_price || decision.minimum_recommended_price || v.quick_sale_price;
  const resistance = v.resistance_price || decision.resistance_price || v.probable_ceiling || v.negotiation_ceiling;
  const defense = v.price_defense_arguments || decision.price_defense_arguments || [];

  return (
    <ReportBlock eyebrow="Estratégia de Venda" title="Orientação para anunciar, negociar e defender o valor">
      <div className="mcv-report-sales-summary">
        <strong>{v.seller_summary || decision.seller_summary || 'Use a faixa recomendada como referência principal de negociação.'}</strong>
        <p>{v.stuck_risk_reason || decision.stuck_risk_reason || 'Acima da faixa recomendada, anúncios semelhantes podem perder competitividade.'}</p>
      </div>
      <ExecutiveTable
        columns={['Decisão', 'Valor', 'Como usar']}
        rows={[
          ['Preço para anunciar', fmtCurrency(listing || 0), 'Valor de entrada para o anúncio'],
          ['Faixa ideal para fechar', `${fmtCurrency(closeMin || 0)} a ${fmtCurrency(closeMax || 0)}`, 'Intervalo saudável para aceitar proposta'],
          ['Evite aceitar abaixo de', fmtCurrency(minimum || 0), 'Ponto de atenção para não perder margem'],
          ['Teto com baixa liquidez', fmtCurrency(resistance || 0), 'Acima disso, tende a haver mais resistência'],
          ['Revisar preço após', `${v.review_price_after_days || decision.review_price_after_days || 10} dias`, `Reduzir ${v.suggested_price_cut_percent || decision.suggested_price_cut_percent || 2}% a 3% se houver baixa procura`],
        ]}
      />
      <div className="mcv-defense-list">
        <h3>Como defender esse valor</h3>
        {defense.slice(0, 5).map((item) => <p key={item}>{item}</p>)}
      </div>
    </ReportBlock>
  );
}
