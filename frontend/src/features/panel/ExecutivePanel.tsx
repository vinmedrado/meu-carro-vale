import { Database, FileText, Gauge, HandCoins } from 'lucide-react';
import type { ValuationResult } from '../../types';
import { fmtCurrency } from '../../lib/format';
import { getRecommendedTopPrice } from '../../lib/valuationAccessors';
import { ConfidenceBadge, ExecutiveTable, LiquidityBadge, MarketTemperatureBar, MethodologyBox, MetricLine, ValuationRange } from '../../design-system/dashboard';
import { SalesStrategyPanel } from './SalesStrategyPanel';

export function ExecutivePanel({ result }: { result: ValuationResult | null }) {
  const v = result?.valuation;
  const ideal = v?.ideal_price ?? 89400;
  const quick = v?.quick_sale_price ?? 82900;
  const recommendedTop = v ? getRecommendedTopPrice(v) : 96100;
  const fipe = v?.fipe_real || v?.fipe_simulated || 80300;
  const indexValue = v?.vehicle_score ?? 91;
  const liquidity = v?.liquidity_score ?? indexValue;
  const confidence = v?.confidence_score ?? 88;
  const demandIndex = v?.demand_index ?? liquidity;
  const marketTemperature = v?.market_temperature_label ?? v?.market_temperature ?? 'Equilibrado';
  const saleVelocity = v?.sale_velocity ?? 'normal';
  const comparables = v?.comparables_used ?? v?.comparable_count ?? 12;
  const delta = v?.market_delta_vs_fipe_pct ?? Math.round(((ideal - fipe) / fipe) * 100);

  return (
    <section id="painel" className="mcv-executive-panel">
      <div className="mcv-page-intro">
        <div>
          <p>Centro de inteligência automotiva</p>
          <h2>Painel executivo do veículo</h2>
          <span>FIPE, comparáveis, liquidez e negociação em uma leitura única.</span>
        </div>
        <div className="mcv-intro-actions">
          <ConfidenceBadge value={confidence} />
          <LiquidityBadge label={v?.liquidity_label || 'Liquidez boa'} value={liquidity} />
        </div>
      </div>

      <ValuationRange quick={quick} ideal={ideal} recommendedTop={recommendedTop} />

      <SalesStrategyPanel result={result} />

      <div className="mcv-metrics-row">
        <MetricLine label="Índice Meu Carro Vale" value={`${indexValue}/100`} tone="green" note="força comercial" />
        <MetricLine label="Potencial de negociação" value={fmtCurrency(Math.max(0, ideal - quick))} tone="gold" />
        <MetricLine label="Comparáveis usados" value={String(comparables)} note="base do cálculo" />
        <MetricLine label="Temperatura" value={marketTemperature} note={`${demandIndex}/100 demanda`} />
        <MetricLine label="Diferença vs FIPE" value={`${delta > 0 ? '+' : ''}${delta}%`} tone={delta >= 0 ? 'green' : 'danger'} />
      </div>

      <div className="mcv-panel-split">
        <section className="mcv-panel-document">
          <div className="mcv-section-title"><p>Fonte dos dados</p><h2>Base da análise</h2></div>
          <ExecutiveTable
            columns={['Indicador', 'Leitura', 'Uso na decisão']}
            rows={[
              ['FIPE', fmtCurrency(fipe), 'Piso técnico de referência'],
              ['Mercado atual', fmtCurrency(v?.market_reference || ideal), 'Preço observado nos comparáveis'],
              ['Venda rápida', fmtCurrency(quick), 'Faixa para liquidez maior'],
              ['Valor indicado', fmtCurrency(ideal), 'Âncora principal de negociação'],
            ]}
          />
        </section>
        <section className="mcv-panel-document">
          <div className="mcv-section-title"><p>Leitura comercial</p><h2>Resumo de decisão</h2></div>
          <MarketTemperatureBar label={marketTemperature} value={v?.market_temperature_score ?? demandIndex} />
          <div className="mcv-decision-list">
            <Decision icon={<Gauge size={16}/>} title="Liquidez" text={v?.liquidity_explanation || `Mercado ${marketTemperature.toLowerCase()}, velocidade de venda ${saleVelocity} e demanda ${demandIndex}/100.`} />
            <Decision icon={<HandCoins size={16}/>} title="Negociação" text={v?.recommended_listing_price ? `Anuncie próximo de ${fmtCurrency(v.recommended_listing_price)} e use ${fmtCurrency(v.quick_sale_price)} para venda rápida.` : result?.insights?.negotiation_recommendation || 'Use o valor indicado como âncora e preserve margem para proposta.'} />
            <Decision icon={<Database size={16}/>} title="Dados" text={v?.executive_market_insight_v2 || v?.methodology_note || 'A análise cruza referência FIPE, comparáveis e características do veículo.'} />
          </div>
        </section>
      </div>

      <section className="mcv-panel-document">
        <div className="mcv-section-title"><p>Metodologia</p><h2>Critérios aplicados no cálculo</h2></div>
        <MethodologyBox items={[
          { label: 'Região', value: v?.regional_scope || (result ? `${result.vehicle.city}/${result.vehicle.state}` : 'Praça informada') },
          { label: 'Amostra', value: `${comparables} comparáveis` },
          { label: 'Similaridade', value: `${v?.similarity_score ?? v?.average_similarity_score ?? '-'} / 100` },
          { label: 'Regional', value: `${v?.regional_market_temperature ?? marketTemperature}` },
          { label: 'Peso mercado', value: `${Math.round((v?.real_market_weight ?? 0.82) * 100)}%` },
          { label: 'Peso FIPE', value: `${Math.round((v?.fipe_weight ?? 0.18) * 100)}%` },
        ]} />
      </section>

      {!result ? (
        <section className="mcv-empty-state">
          <FileText size={18}/>
          <div><strong>Preencha o veículo para gerar o laudo.</strong><p>O resultado aparecerá aqui com faixa de valor, índice, comparáveis e metodologia.</p></div>
        </section>
      ) : null}
    </section>
  );
}

function Decision({ icon, title, text }: { icon: React.ReactNode; title: string; text: string }) {
  return <div className="mcv-decision-item"><span>{icon}</span><div><strong>{title}</strong><p>{text}</p></div></div>;
}
