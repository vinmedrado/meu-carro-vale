import { LiquidityBadge, MarketTemperatureBar, ReportBlock } from '../../../design-system/report';
import type { ValuationResult } from '../../../types';

export function LiquidityAnalysis({ result }: { result: ValuationResult }) {
  const v = result.valuation;
  return (
    <div className="mcv-report-two-cols">
      <ReportBlock eyebrow="Índice Meu Carro Vale" title="Força comercial">
        <div className="mcv-index-line"><strong>{v.vehicle_score}</strong><span>de 100</span></div>
        <p className="mcv-muted-text">Índice composto por liquidez, região, quilometragem, preço, comparáveis e qualidade da amostra.</p>
      </ReportBlock>
      <ReportBlock eyebrow="Liquidez" title="Facilidade esperada de venda">
        <MarketTemperatureBar label={v.market_temperature_label || v.market_temperature || 'Estável'} value={v.market_temperature_score || v.demand_index || v.liquidity_score || v.vehicle_score} />
        <LiquidityBadge label={v.liquidity_level || v.liquidity_label || 'Liquidez em análise'} value={v.sale_probability || v.demand_index || v.liquidity_score || v.vehicle_score} />
        <p className="mcv-muted-text">{v.market_temperature_detail || `Mercado ${String(v.market_temperature || 'equilibrado').toLowerCase()}, velocidade ${String(v.sale_velocity || 'normal').toLowerCase()} e confiança ${v.confidence_level || v.confidence_label || 'em análise'}.`}</p>
        {v.negotiation_intelligence?.estimated_sale_time ? <p className="mcv-muted-text">Tempo médio estimado: {v.negotiation_intelligence.estimated_sale_time}.</p> : null}
        {v.estimated_market_resistance ? <p className="mcv-muted-text">Resistência estimada: {v.estimated_market_resistance}.</p> : null}
      </ReportBlock>
    </div>
  );
}
