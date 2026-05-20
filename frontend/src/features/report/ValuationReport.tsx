import { useMemo, useState } from 'react';
import type { ValuationResult } from '../../types';
import { fmtCurrency } from '../../lib/format';
import { getRecommendedTopPrice } from '../../lib/valuationAccessors';
import { exportReportPdf } from './report/PdfExport';
import { Toast } from './reportSections';

type Tab = 'resumo' | 'estrategia' | 'comparaveis' | 'mercado' | 'laudo';

const tabs: { id: Tab; label: string }[] = [
  { id: 'resumo', label: 'Resumo' },
  { id: 'estrategia', label: 'Estratégia de Venda' },
  { id: 'comparaveis', label: 'Comparáveis' },
  { id: 'mercado', label: 'Mercado' },
  { id: 'laudo', label: 'Laudo' },
];

export function ValuationReport({ result }: { result: ValuationResult }) {
  const [active, setActive] = useState<Tab>('resumo');
  const [exporting, setExporting] = useState(false);
  const [toast, setToast] = useState('');
  const v = result.valuation;

  const data = useMemo(() => {
    const listing = v.selling_decision?.listing_price ?? v.listing_price ?? v.recommended_listing_price ?? v.selling_strategy?.recommended_listing_price ?? getRecommendedTopPrice(v);
    const ideal = v.ideal_price ?? v.market_reference ?? listing;
    const quick = v.quick_sale_price ?? v.selling_strategy?.quick_sale_price ?? Math.round(ideal * 0.94);
    const min = v.selling_decision?.minimum_recommended_price ?? v.minimum_recommended_price ?? v.negotiation_floor ?? quick;
    const closeMin = v.selling_decision?.ideal_close_range_min ?? v.safe_price_range?.[0] ?? v.negotiation_range?.[0] ?? quick;
    const closeMax = v.selling_decision?.ideal_close_range_max ?? v.safe_price_range?.[1] ?? v.negotiation_range?.[1] ?? ideal;
    const reviewDays = v.selling_decision?.review_price_after_days ?? v.review_price_after_days ?? 12;
    const risk = v.selling_decision?.stuck_risk_level ?? v.stuck_risk_level ?? v.liquidity_pressure?.estimated_market_resistance ?? v.estimated_market_resistance ?? 'Médio';
    const confidence = v.confidence_score ?? 88;
    const liquidity = v.liquidity_label ?? v.liquidity_level ?? 'Boa';
    const temperature = v.market_insights?.market_temperature_label ?? v.market_temperature_label ?? v.market_temperature ?? 'Equilibrado';
    const pressure = v.price_positioning?.pricing_pressure ?? v.pricing_pressure ?? 'Moderada';
    const trend = v.trend_direction ?? v.weekly_trend ?? v.monthly_trend ?? 'Estável';
    return { listing, ideal, quick, min, closeMin, closeMax, reviewDays, risk, confidence, liquidity, temperature, pressure, trend };
  }, [v]);

  function showToast(message: string) {
    setToast(message);
    window.setTimeout(() => setToast(''), 2200);
  }

  async function handleExportPdf() {
    setExporting(true);
    showToast('Gerando PDF...');
    await exportReportPdf(result);
    setExporting(false);
    showToast('PDF baixado.');
  }

  const comparables = v.comparables?.length ? v.comparables : [];
  const comparableAnalysis = v.comparable_analysis?.length ? v.comparable_analysis : [];

  return (
    <section id="relatorio" className="mcv-result-shell-clean">
      <header className="mcv-result-header-clean">
        <div>
          <p className="mcv-kicker">Resultado</p>
          <h2>{result.vehicle.brand} {result.vehicle.model}</h2>
          <span>{result.vehicle.year} • {result.vehicle.city}/{result.vehicle.state}</span>
        </div>
        <button className="mcv-download-top" onClick={handleExportPdf} disabled={exporting}>{exporting ? 'Gerando...' : 'Baixar PDF'}</button>
      </header>

      <nav className="mcv-result-tabs-clean" aria-label="Abas do resultado">
        {tabs.map((tab) => <button key={tab.id} onClick={() => setActive(tab.id)} className={active === tab.id ? 'active' : ''}>{tab.label}</button>)}
      </nav>

      <div className="mcv-result-body-clean">
        {active === 'resumo' ? (
          <section className="mcv-summary-grid-clean">
            <Metric label="Valor recomendado" value={fmtCurrency(data.ideal)} strong />
            <Metric label="Preço para anunciar" value={fmtCurrency(data.listing)} />
            <Metric label="Menor valor recomendado" value={fmtCurrency(data.min)} />
            <Metric label="Confiança da análise" value={`${data.confidence}%`} />
            <Metric label="Risco de ficar parado" value={String(data.risk)} />
          </section>
        ) : null}

        {active === 'estrategia' ? (
          <section className="mcv-strategy-list-clean">
            <Item title="Preço para anunciar" text={`Anuncie por ${fmtCurrency(data.listing)}.`} />
            <Item title="Faixa ideal para fechar" text={`${fmtCurrency(data.closeMin)} a ${fmtCurrency(data.closeMax)}.`} />
            <Item title="Proposta mínima" text={`Não aceite abaixo de ${fmtCurrency(data.min)}.`} />
            <Item title="Quando baixar" text={`Revise após ${data.reviewDays} dias.`} />
            <Item title="Como defender" text={firstText(v.selling_decision?.price_defense_arguments ?? v.price_defense_arguments, result.insights?.negotiation_recommendation || 'Use histórico, estado e comparáveis.')} />
          </section>
        ) : null}

        {active === 'comparaveis' ? (
          <section id="comparaveis" className="mcv-comparables-clean">
            <div className="mcv-table-wrap-clean">
              <table>
                <thead><tr><th>Veículo</th><th>Ano</th><th>KM</th><th>Cidade</th><th>Preço</th><th>Similaridade</th><th>Impacto</th></tr></thead>
                <tbody>
                  {comparables.length ? comparables.slice(0, 10).map((item, index) => (
                    <tr key={`${item.title}-${index}`}><td>{item.title}</td><td>{item.year}</td><td>{item.mileage?.toLocaleString('pt-BR')}</td><td>{item.city}/{item.state}</td><td>{fmtCurrency(item.price)}</td><td>{item.similarity_score}%</td><td>{impactLabel(item.price, data.ideal)}</td></tr>
                  )) : comparableAnalysis.slice(0, 10).map((item, index) => (
                    <tr key={`${item.title}-${index}`}><td>{item.title || 'Comparável'}</td><td>-</td><td>{item.km_difference?.toLocaleString('pt-BR')}</td><td>{item.source || '-'}</td><td>{fmtCurrency(item.price)}</td><td>{item.similarity_score}%</td><td>{fmtCurrency(item.valuation_impact || 0)}</td></tr>
                  ))}
                  {!comparables.length && !comparableAnalysis.length ? <tr><td colSpan={7}>Nenhum comparável retornado.</td></tr> : null}
                </tbody>
              </table>
            </div>
          </section>
        ) : null}

        {active === 'mercado' ? (
          <section className="mcv-market-grid-clean">
            <Metric label="Liquidez" value={String(data.liquidity)} />
            <Metric label="Temperatura" value={String(data.temperature)} />
            <Metric label="Resistência" value={String(data.pressure)} />
            <Metric label="Tendência" value={String(data.trend)} />
            <Metric label="Pressão de mercado" value={String(v.pressure_score ?? v.liquidity_pressure?.pressure_score ?? '-')} />
          </section>
        ) : null}

        {active === 'laudo' ? (
          <section id="laudo" className="mcv-report-actions-clean">
            <div>
              <h3>Resumo do laudo</h3>
              <p>{shortText(result.insights?.summary || v.seller_summary || 'Análise pronta para negociação.')}</p>
            </div>
            <div className="mcv-report-buttons-clean">
              <button onClick={handleExportPdf} disabled={exporting}>{exporting ? 'Gerando...' : 'Baixar PDF'}</button>
              <button onClick={() => showToast('Análise salva.')}>Salvar análise</button>
            </div>
          </section>
        ) : null}
      </div>
      <Toast message={toast} />
    </section>
  );
}

function Metric({ label, value, strong = false }: { label: string; value: string; strong?: boolean }) {
  return <article className={strong ? 'mcv-metric-clean strong' : 'mcv-metric-clean'}><span>{label}</span><strong>{value}</strong></article>;
}

function Item({ title, text }: { title: string; text: string }) {
  return <article><span>{title}</span><strong>{shortText(text)}</strong></article>;
}

function shortText(text: string) { return text.length > 95 ? `${text.slice(0, 92)}...` : text; }
function firstText(values: string[] | undefined, fallback: string) { return shortText(values?.find(Boolean) || fallback); }
function impactLabel(price: number, ideal: number) { const diff = price - ideal; if (Math.abs(diff) < 500) return 'Neutro'; return diff > 0 ? 'Puxa para cima' : 'Puxa para baixo'; }
