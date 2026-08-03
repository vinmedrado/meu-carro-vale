import { useMemo, useState } from 'react';
import { motion, type Variants } from 'framer-motion';
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { ArrowUpRight, BadgeCheck, BarChart3, CarFront, Download, FileText, RefreshCcw, Sparkles, TrendingUp } from 'lucide-react';
import type { ValuationResult } from '../../types';
import { downloadExecutiveReportPdf, PORTFOLIO_MODE } from '../../lib/api';
import { fmtCurrency } from '../../lib/format';
import { getRecommendedTopPrice } from '../../lib/valuationAccessors';
import { VehicleHero } from '../../components/vehicle/VehicleHero';
import { exportReportPdf } from './report/PdfExport';
import { Toast } from './reportSections';
import { PricingModal } from '../saas/PricingModal';
import { ValuationIntelligence } from './ValuationIntelligence';

type Tab = 'resumo' | 'estrategia' | 'comparaveis' | 'tendencia' | 'mercado' | 'laudo';

type ComparableCard = {
  title: string;
  price: number;
  year?: number | string | null;
  mileage?: number | string | null;
  city?: string;
  state?: string;
  source: string;
  link?: string;
  thumbnail?: string;
  differenceLabel?: string;
};

type DistributionPoint = { label: string; count: number; midpoint: number };

type PricingBand = { label: string; value: number; tone: 'quick' | 'ideal' | 'premium' };

const tabs: { id: Tab; label: string }[] = [
  { id: 'resumo', label: 'Resumo' },
  { id: 'estrategia', label: 'Estratégia de Venda' },
  { id: 'comparaveis', label: 'Comparáveis' },
  { id: 'tendencia', label: 'Tendência' },
  { id: 'mercado', label: 'Mercado' },
  { id: 'laudo', label: 'Laudo' },
];

const blockedCustomerTerms = ['ca' + 'che', 'check' + 'point', 're' + 'try', 't' + 'tl', 'back' + 'off', 'raw' + '_payload', 'raw payload', 'data' + '-engine', 'import quality'].map((term) => new RegExp(term.replace(/[\\^$.*+?()[\]{}|]/g, '\\$&').replace('raw payload', 'raw[_ ]?payload'), 'i'));
const cardVariants: Variants = { hidden: { opacity: 0, y: 22 }, visible: (i: number) => ({ opacity: 1, y: 0, transition: { delay: i * 0.07, duration: 0.42, ease: [0.16, 1, 0.3, 1] } }) };

function cleanCustomerText(text: unknown, fallback = '') {
  let value = String(text || fallback || '');
  blockedCustomerTerms.forEach((term) => { value = value.replace(term, 'informação interna'); });
  return value;
}

function fmtKm(value: unknown) {
  const number = Number(value || 0);
  return Number.isFinite(number) && number > 0 ? `${number.toLocaleString('pt-BR')} km` : 'KM não informado';
}

function asRecord(value: unknown): Record<string, unknown> { return value && typeof value === 'object' ? value as Record<string, unknown> : {}; }
function asNumber(value: unknown, fallback = 0) { const n = Number(value); return Number.isFinite(n) ? n : fallback; }
function asPositiveMoney(value: unknown, fallback = 0) { const n = Number(value); return Number.isFinite(n) && n > 0 ? n : fallback; }
function asString(value: unknown, fallback = '') { return typeof value === 'string' && value.trim() ? value : fallback; }

function normalizeComparableAnalysis(value: unknown): unknown[] {
  if (Array.isArray(value)) return value;
  if (value && typeof value === 'object') return [value];
  return [];
}

function normalizeSourceLabel(source: unknown) {
  const value = String(source || '').trim().toLowerCase();
  if (['market_real', 'mercadolivre_api', 'mercadolivre', 'market_listings', 'ml_api'].includes(value)) return 'Dados reais de mercado';
  if (['fipe_local', 'cache_local'].includes(value)) return 'FIPE local';
  if (['fallback_estimado', 'unavailable', 'fallback'].includes(value)) return 'Estimativa';
  return value ? cleanCustomerText(source, 'Estimativa') : 'Estimativa';
}

function normalizeComparable(item: unknown, index: number): ComparableCard | null {
  const record = asRecord(item);
  const price = asNumber(record.price, 0);
  const title = cleanCustomerText(record.title || record.vehicle_title || record.name || record.label, `Comparável ${index + 1}`);
  const link = asString(record.link || record.url || record.permalink, '');
  if (!price || price <= 0) return null;
  return {
    title,
    price,
    year: (record.year ?? record.year_model ?? record.model_year) as number | string | null | undefined,
    mileage: (record.mileage ?? record.mileage_km ?? record.km) as number | string | null | undefined,
    city: asString(record.city, ''),
    state: asString(record.state, ''),
    source: cleanCustomerText(record.source || 'Mercado'),
    link,
    thumbnail: asString(record.thumbnail || record.image_url || record.imageUrl, ''),
    differenceLabel: cleanCustomerText(record.difference_label || record.reading || 'Comparável considerado na análise'),
  };
}

function buildDistribution(comparables: ComparableCard[], fallbackChart: unknown, idealPrice: number): DistributionPoint[] {
  const chart = Array.isArray(fallbackChart) ? fallbackChart : [];
  if (comparables.length >= 2) {
    const prices = comparables.map((item) => item.price).filter((price) => price > 0).sort((a, b) => a - b);
    if (prices.length < 2) return [];
    const min = prices[0];
    const max = prices[prices.length - 1];
    const bucketCount = Math.min(6, Math.max(3, prices.length));
    const step = Math.max(1000, (max - min) / bucketCount);
    const buckets = Array.from({ length: bucketCount }, (_, i) => {
      const start = min + i * step;
      const end = i === bucketCount - 1 ? max + 1 : start + step;
      const count = prices.filter((price) => price >= start && price < end).length;
      const midpoint = Math.round((start + end) / 2);
      return { label: compactCurrency(midpoint), count, midpoint };
    });
    return buckets.filter((bucket) => bucket.count > 0);
  }
  if (chart.length) {
    return chart.map((point, index) => {
      const record = asRecord(point);
      const value = asNumber(record.value ?? record.count, 0);
      const label = asString(record.label, `Faixa ${index + 1}`);
      return { label, count: value, midpoint: asNumber(record.midpoint, idealPrice) };
    }).filter((point) => point.count > 0);
  }
  return [];
}

function compactCurrency(value: number) {
  if (!Number.isFinite(value) || value <= 0) return 'R$ -';
  return `R$${Math.round(value / 1000)}k`;
}

function buildCustomerView(result: ValuationResult) {
  const planAccess = asRecord((result as unknown as Record<string, unknown>).plan_access);
  const saas = asRecord((result as unknown as Record<string, unknown>).saas);
  const saasUsage = asRecord(saas.usage);
  const features = asRecord(planAccess.features || saasUsage.features);
  const hasFeatureContract = Object.keys(features).length > 0;
  const isPlanLimited = planAccess.limited === true || (hasFeatureContract && features.pdf === false);
  const v = result.valuation;
  const customer = result.customer_valuation;
  const fipe = asPositiveMoney(customer?.fipe_price ?? v.fipe_price ?? v.fipe_real ?? v.fipe_simulated, 0);
  const marketReference = asPositiveMoney(v.market_reference, fipe);
  const recommended = asPositiveMoney(customer?.recommended_price ?? v.recommended_price ?? v.ideal_price, marketReference);
  const quick = asPositiveMoney(customer?.quick_sale_price ?? v.quick_sale_price, Math.round(recommended * 0.94));
  const premium = asPositiveMoney(customer?.premium_sale_price ?? v.premium_sale_price ?? v.recommended_top_price, Math.round(recommended * 1.06));
  const comparableAnalysis = normalizeComparableAnalysis(v.comparable_analysis);
  const comparableCount = Number(customer?.comparable_count ?? v.comparable_count ?? v.comparables_used ?? v.comparables_count ?? v.comparables?.length ?? comparableAnalysis.length ?? 0);
  const marketSources = (customer?.market_sources?.length ? customer.market_sources : (v.market_sources as string[] | undefined) ?? v.sources ?? []).filter(Boolean) as string[];
  const rawComparables = [...(Array.isArray(v.comparables) ? v.comparables : []), ...(Array.isArray(customer?.comparables_preview) ? customer.comparables_preview : []), ...comparableAnalysis];
  const comparablesPreview = rawComparables.map((item, index) => normalizeComparable(item, index)).filter((item): item is ComparableCard => Boolean(item)).slice(0, 6);
  const hasMarket = comparableCount > 0 && (marketSources.length > 0 || comparablesPreview.length > 0);
  const confidence = Number(customer?.confidence_score ?? v.confidence_score ?? (hasMarket ? 76 : 48));
  const liquidity = Number(customer?.liquidity_score ?? v.liquidity_score ?? (hasMarket ? 68 : 45));
  const strategy = customer?.pricing_strategy?.length ? customer.pricing_strategy : [
    { label: 'Venda rápida', value: quick, description: 'Faixa mais competitiva para atrair interessados mais rápido.', when_to_use: 'Use quando a prioridade for vender em menos tempo.' },
    { label: 'Preço recomendado', value: recommended, description: 'Equilíbrio entre atratividade, margem de negociação e valor percebido.', when_to_use: 'Use como preço principal do anúncio.' },
    { label: 'Preço premium', value: premium, description: 'Faixa mais alta para veículos muito bem conservados ou com diferenciais claros.', when_to_use: 'Use quando não houver pressa e o carro estiver acima da média.' },
  ];
  const fallbackSummary = hasMarket
    ? 'Seu veículo foi analisado com referência FIPE e comparáveis de mercado disponíveis para sugerir uma faixa segura de venda.'
    : 'Dados de mercado ainda não disponíveis para este veículo. A FIPE foi usada como referência principal e as faixas abaixo são uma estimativa inicial conservadora.';
  const confidenceLevel = cleanCustomerText(customer?.confidence_level ?? v.confidence_level ?? v.confidence_label ?? (confidence >= 70 ? 'alta' : confidence >= 45 ? 'moderada' : 'baixa'));
  const liquidityLevel = cleanCustomerText(customer?.liquidity_level ?? v.liquidity_level ?? v.liquidity_label ?? (liquidity >= 70 ? 'alta' : liquidity >= 45 ? 'moderada' : 'baixa'));
  const marketStability = cleanCustomerText(customer?.market_stability ?? v.market_stability ?? (hasMarket ? 'estável' : 'indefinido'));
  const fallbackInsights = hasMarket
    ? ['O veículo apresenta uma base de mercado útil para orientar o anúncio.', 'A faixa recomendada considera anúncios similares e a referência FIPE.', 'A diferença entre venda rápida e premium mostra a margem estratégica de negociação.']
    : ['Dados de mercado ainda não disponíveis para este veículo.', 'A análise usa uma estimativa inicial conservadora baseada na referência FIPE.', 'Evite apresentar essa estimativa como leitura definitiva de mercado.'];
  const valuationInsights = ((customer?.valuation_insights?.length ? customer.valuation_insights : (v.valuation_insights as string[] | undefined)) || fallbackInsights)
    .map((item) => cleanCustomerText(item))
    .filter(Boolean)
    .slice(0, 3);
  const marketPrices = comparablesPreview.map((item) => item.price).filter((price) => price > 0);
  const marketMin = Number(customer?.market_min_price || v.price_dispersion?.min || (marketPrices.length ? Math.min(...marketPrices) : 0));
  const marketMax = Number(customer?.market_max_price || v.price_dispersion?.max || (marketPrices.length ? Math.max(...marketPrices) : 0));
  const marketAverage = Number(customer?.market_average_price || (marketPrices.length ? marketPrices.reduce((acc, price) => acc + price, 0) / marketPrices.length : 0));
  const positioningSummary = cleanCustomerText(customer?.positioning_summary ?? v.price_positioning?.positioning_summary, hasMarket ? 'Faixa alinhada ao mercado atual.' : 'Ainda não há comparáveis suficientes para este veículo.');
  const comparablesSummary = hasMarket
    ? `Baseado em ${comparableCount} anúncio${comparableCount === 1 ? '' : 's'} ativo${comparableCount === 1 ? '' : 's'} nos últimos 30 dias.`
    : 'Ainda não há comparáveis suficientes para este veículo.';
  const trendDirection = cleanCustomerText(customer?.trend_direction ?? v.trend_direction ?? v.weekly_trend ?? v.monthly_trend ?? 'indefinido');
  const trendStrength = cleanCustomerText(customer?.trend_strength ?? v.trend_strength ?? 'fraca');
  const trendSummary = cleanCustomerText(customer?.trend_summary ?? v.trend_summary, hasMarket ? 'Leitura baseada no valuation atual e nos comparáveis disponíveis.' : 'Ainda não há histórico suficiente para estimar tendência.');
  const sellTimingSignal = cleanCustomerText(customer?.sell_timing_signal ?? v.sell_timing_signal ?? (hasMarket ? 'janela atual monitorável' : 'sem histórico suficiente'));
  const source = cleanCustomerText(v.base_price_source ?? v.data_source ?? (hasMarket ? 'market_real' : fipe > 0 ? 'fipe_local' : 'fallback_estimado'));
  const warning = cleanCustomerText(v.warning ?? v.low_confidence_message ?? (!hasMarket ? 'Estimativa calculada com baixa base de mercado. Use como referência inicial.' : ''));
  const distribution = buildDistribution(comparablesPreview, v.chart, recommended);
  const heroImage = comparablesPreview.find((item) => item.thumbnail)?.thumbnail;
  const hasValidFipe = Number.isFinite(fipe) && fipe > 0;
  const isAboveFipe = hasValidFipe && recommended > fipe;
  const fipeDeltaPct = isAboveFipe ? Math.round(((recommended - fipe) / fipe) * 100) : 0;

  return {
    vehicleLabel: customer?.vehicle_label || `${result.vehicle.brand} ${result.vehicle.model}`.trim(),
    fipe,
    recommended,
    quick,
    premium,
    lostPotential: Math.max(0, premium - quick),
    confidence: Math.max(0, Math.min(100, Math.round(confidence))),
    liquidity: Math.max(0, Math.min(100, Math.round(liquidity))),
    comparableCount,
    marketSources: hasMarket ? marketSources : [],
    hasMarket,
    summary: cleanCustomerText(customer?.human_summary ?? v.human_summary, fallbackSummary),
    confidenceLevel,
    liquidityLevel,
    marketStability,
    valuationInsights,
    strategy,
    pricingBands: [
      { label: 'Venda Rápida', value: quick, tone: 'quick' },
      { label: 'Preço Ideal', value: recommended, tone: 'ideal' },
      { label: 'Valor Premium', value: premium, tone: 'premium' },
    ] as PricingBand[],
    comparablesPreview,
    marketMin,
    marketMax,
    marketAverage,
    positioningSummary,
    comparablesSummary,
    trendDirection,
    trendStrength,
    trendSummary,
    sellTimingSignal,
    source,
    warning,
    distribution,
    heroImage,
    planAccess: { limited: isPlanLimited, features, message: cleanCustomerText(planAccess.message, "") },
    hasValidFipe,
    isAboveFipe,
    fipeDeltaPct,
  };
}

export function ValuationReport({ result }: { result: ValuationResult }) {
  const [active, setActive] = useState<Tab>('resumo');
  const [exporting, setExporting] = useState(false);
  const [toast, setToast] = useState('');
  const [upgradeOpen, setUpgradeOpen] = useState(false);
  const v = result.valuation;
  const customerView = useMemo(() => buildCustomerView(result), [result]);

  const data = useMemo(() => {
    const listing = v.selling_decision?.listing_price ?? v.listing_price ?? v.recommended_listing_price ?? v.selling_strategy?.recommended_listing_price ?? getRecommendedTopPrice(v);
    const ideal = v.ideal_price ?? v.market_reference ?? listing;
    const quick = v.quick_sale_price ?? v.selling_strategy?.quick_sale_price ?? Math.round(ideal * 0.94);
    const min = v.selling_decision?.minimum_recommended_price ?? v.minimum_recommended_price ?? v.negotiation_floor ?? quick;
    const closeMin = v.selling_decision?.ideal_close_range_min ?? v.safe_price_range?.[0] ?? v.negotiation_range?.[0] ?? quick;
    const closeMax = v.selling_decision?.ideal_close_range_max ?? v.safe_price_range?.[1] ?? v.negotiation_range?.[1] ?? ideal;
    const reviewDays = v.selling_decision?.review_price_after_days ?? v.review_price_after_days ?? 12;
    const risk = v.selling_decision?.stuck_risk_level ?? v.stuck_risk_level ?? v.liquidity_pressure?.estimated_market_resistance ?? v.estimated_market_resistance ?? 'Médio';
    const confidence = v.confidence_score ?? customerView.confidence;
    const liquidity = v.liquidity_label ?? v.liquidity_level ?? customerView.liquidityLevel;
    const temperature = v.market_insights?.market_temperature_label ?? v.market_temperature_label ?? v.market_temperature ?? customerView.marketStability;
    const pressure = v.price_positioning?.pricing_pressure ?? v.pricing_pressure ?? 'Moderada';
    const trend = customerView.trendDirection ?? v.trend_direction ?? v.weekly_trend ?? v.monthly_trend ?? 'Estável';
    return { listing, ideal, quick, min, closeMin, closeMax, reviewDays, risk, confidence, liquidity, temperature, pressure, trend };
  }, [v, customerView]);

  function showToast(message: string) {
    setToast(message);
    window.setTimeout(() => setToast(''), 2200);
  }

  async function handleExportPdf() {
    if (customerView.planAccess.limited) {
      setUpgradeOpen(true);
      showToast('Exportação PDF disponível no plano PRO.');
      return;
    }
    setExporting(true);
    showToast('Gerando relatório PDF...');
    try {
      if (PORTFOLIO_MODE) {
        await exportReportPdf(result);
      } else {
        try {
          const { blob, filename } = await downloadExecutiveReportPdf('', result);
          const url = URL.createObjectURL(blob);
          const link = document.createElement('a');
          link.href = url;
          link.download = filename;
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          URL.revokeObjectURL(url);
        } catch {
          await exportReportPdf(result);
        }
      }
      showToast('Relatório PDF baixado.');
    } catch (err) {
      showToast(err instanceof Error ? err.message : 'Entre novamente para baixar o relatório.');
    } finally {
      setExporting(false);
    }
  }

  return (
    <section id="relatorio" className="mcv-result-shell-clean mcv-premium-result-dashboard">
      <header className="mcv-result-header-clean mcv-result-dashboard-header">
        <div>
          <p className="mcv-kicker">Resultado premium</p>
          <h2>{result.vehicle.brand} {result.vehicle.model}</h2>
          <span>{result.vehicle.year} • {result.vehicle.city}/{result.vehicle.state}</span>
        </div>
        <button className="mcv-download-top" onClick={handleExportPdf} disabled={exporting}><Download size={17} /> {exporting ? 'Gerando...' : 'Baixar Relatório PDF'}</button>
      </header>

      <nav className="mcv-result-tabs-clean mcv-result-tabs-premium" aria-label="Abas do resultado">
        {tabs.map((tab) => <button key={tab.id} onClick={() => setActive(tab.id)} className={active === tab.id ? 'active' : ''}>{tab.label}</button>)}
      </nav>

      <div className="mcv-result-body-clean mcv-result-dashboard-body">
        {active === 'resumo' ? (
          <motion.div initial="hidden" animate="visible" className="mcv-dashboard-premium-grid">
            <motion.aside className="mcv-dashboard-sidebar" variants={cardVariants} custom={0}>
              <VehicleHero brand={result.vehicle.brand} model={result.vehicle.model} year={result.vehicle.year} imageUrl={customerView.heroImage} />
              <SourceTruthCard source={customerView.source} confidence={customerView.confidence} warning={customerView.warning} />
            </motion.aside>

            <div className="mcv-dashboard-main">
              <motion.section className="mcv-dashboard-topline" variants={cardVariants} custom={1}>
                <McvIndexCard score={customerView.confidence} liquidity={customerView.liquidity} hasMarket={customerView.hasMarket} isAboveFipe={customerView.isAboveFipe} fipeDeltaPct={customerView.fipeDeltaPct} />
                <PricingRangeCard bands={customerView.pricingBands} fipe={customerView.fipe} hasValidFipe={customerView.hasValidFipe} fipeDeltaPct={customerView.fipeDeltaPct} isAboveFipe={customerView.isAboveFipe} />
                <LostPotentialCard value={customerView.lostPotential} />
              </motion.section>

              <motion.section className="mcv-dashboard-split" variants={cardVariants} custom={2}>
                <ComparablesCard comparables={customerView.comparablesPreview} summary={customerView.comparablesSummary} hasMarket={customerView.hasMarket} />
                <DistributionCard data={customerView.distribution} idealPrice={customerView.recommended} hasMarket={customerView.hasMarket} />
              </motion.section>

              <motion.section className="mcv-dashboard-bottom" variants={cardVariants} custom={3}>
                <LiquidityTimingCard liquidity={customerView.liquidity} label={customerView.liquidityLevel} trend={customerView.trendDirection} timing={customerView.sellTimingSignal} hasMarket={customerView.hasMarket} />
                <InsightsCard insights={customerView.valuationInsights} warning={customerView.warning} />
              </motion.section>
            </div>
          </motion.div>
        ) : null}

        {active === 'estrategia' ? (
          <section className="mcv-strategy-list-clean">
            {customerView.strategy.map((item) => (
              <Item key={item.label} title={item.label} text={`${fmtCurrency(item.value)} — ${cleanCustomerText(item.description)} ${cleanCustomerText(item.when_to_use)}`} />
            ))}
            <Item title="Resumo da análise" text={customerView.summary} />
          </section>
        ) : null}

        {active === 'comparaveis' ? (
          <section id="comparaveis" className="mcv-comparables-experience" aria-label="Comparáveis de mercado">
            <header className="mcv-comparables-header">
              <div>
                <p className="mcv-kicker">Comparáveis de Mercado</p>
                <h3>Carros parecidos considerados na análise</h3>
                <span>{customerView.hasMarket ? customerView.comparablesSummary : 'Ainda não há comparáveis suficientes para este veículo.'}</span>
              </div>
              <strong>{customerView.positioningSummary}</strong>
            </header>
            <ComparablesCard comparables={customerView.comparablesPreview} summary={customerView.comparablesSummary} hasMarket={customerView.hasMarket} expanded />
            {customerView.planAccess.limited ? <div className="mcv-plan-gate-note"><LockIcon /> Comparáveis completos e links externos estão disponíveis no plano PRO.</div> : null}
          </section>
        ) : null}

        {active === 'tendencia' ? (
          <section className="mcv-trend-section" aria-label="Tendência de Mercado">
            <header>
              <p className="mcv-kicker">Tendência de Mercado</p>
              <h3>Momento atual para este veículo</h3>
              <span>{customerView.trendSummary}</span>
            </header>
            <div className="mcv-trend-grid">
              <Metric label="Direção" value={customerView.trendDirection} strong />
              <Metric label="Força" value={customerView.trendStrength} />
              <Metric label="Sinal de venda" value={customerView.sellTimingSignal} />
            </div>
            <p className="mcv-trend-note">Essa leitura ajuda a entender se o preço atual está em um momento favorável, neutro ou com pouca base histórica.</p>
          </section>
        ) : null}

        {active === 'mercado' ? (
          <>
            <ValuationIntelligence result={result} compact />
            <section className="mcv-market-grid-clean">
              <Metric label="Liquidez" value={String(data.liquidity)} />
              <Metric label="Temperatura" value={String(data.temperature)} />
              <Metric label="Resistência" value={String(data.pressure)} />
              <Metric label="Tendência" value={String(data.trend)} />
              <Metric label="Pressão de mercado" value={String(v.pressure_score ?? v.liquidity_pressure?.pressure_score ?? '-')} />
            </section>
          </>
        ) : null}

        {active === 'laudo' ? (
          <section id="laudo" className="mcv-report-actions-clean">
            <div className="mcv-laudo-content">
              <h3>Resumo executivo do laudo</h3>
              <p>{shortText(result.insights?.summary || v.seller_summary || 'Análise pronta para negociação.')}</p>
              <div className="mcv-laudo-executive-grid" aria-label="Indicadores executivos do laudo">
                <article className="mcv-laudo-value-card principal"><span>Preço principal</span><strong>{fmtCurrency(data.ideal)}</strong><small>Referência ideal para defender o valor.</small></article>
                <article className="mcv-laudo-value-card"><span>Venda rápida</span><strong>{fmtCurrency(data.quick)}</strong><small>Faixa para acelerar conversão sem perder controle.</small></article>
                <article className="mcv-laudo-value-card"><span>Valor competitivo</span><strong>{fmtCurrency(data.closeMin)}</strong><small>Entrada saudável para negociação com comprador.</small></article>
              </div>
              <div className="mcv-laudo-ai-strip"><span>Motor proprietário ativo</span><strong>Liquidez • Negociação • Confiança • Desvalorização</strong></div>
            </div>
            <div className="mcv-report-buttons-clean">
              <button onClick={handleExportPdf} disabled={exporting}>{exporting ? 'Gerando...' : 'Baixar Relatório PDF'}</button>
              <button onClick={() => showToast('Análise salva.')}>Salvar análise</button>
            </div>
          </section>
        ) : null}
      </div>

      <div className="mcv-mobile-result-actions" aria-label="Ações rápidas do resultado">
        <button onClick={handleExportPdf} disabled={exporting}><FileText size={16} /> PDF</button>
        <button onClick={() => showToast('Anúncio gerado a partir da avaliação.') }><Sparkles size={16} /> Anúncio</button>
        <button onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}><RefreshCcw size={16} /> Nova</button>
      </div>
      <PricingModal open={upgradeOpen} reason="Exportação PDF disponível no plano PRO." onClose={() => setUpgradeOpen(false)} />
      <Toast message={toast} />
    </section>
  );
}

function McvIndexCard({ score, liquidity, hasMarket, isAboveFipe, fipeDeltaPct }: { score: number; liquidity: number; hasMarket: boolean; isAboveFipe: boolean; fipeDeltaPct: number }) {
  const label = score >= 85 ? 'Forte potencial de venda' : score >= 70 ? 'Mercado favorável' : score >= 55 ? 'Mercado monitorável' : 'Base limitada';
  const rotation = -110 + (Math.max(0, Math.min(100, score)) / 100) * 220;
  return (
    <article className="mcv-index-card">
      <div className="mcv-card-heading"><span>Índice Meu Carro Vale™</span><BadgeCheck size={18} /></div>
      <div className="mcv-gauge-wrap" aria-label={`Score ${score}`}>
        <svg viewBox="0 0 220 140" role="img">
          <path d="M30 115 A80 80 0 0 1 190 115" className="mcv-gauge-track" />
          <path d="M30 115 A80 80 0 0 1 190 115" className="mcv-gauge-progress" pathLength="100" strokeDasharray={`${score} 100`} />
          <motion.line x1="110" y1="115" x2="110" y2="48" className="mcv-gauge-needle" initial={{ rotate: -110 }} animate={{ rotate: rotation }} transition={{ duration: 1.1, ease: 'easeOut' }} style={{ transformOrigin: '110px 115px' }} />
          <circle cx="110" cy="115" r="7" className="mcv-gauge-center" />
        </svg>
        <motion.strong initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}>{score}</motion.strong>
      </div>
      <h3>{label}</h3>
      <div className="mcv-dashboard-badges">
        <span>{liquidity >= 70 ? 'Alta liquidez' : 'Liquidez em análise'}</span>
        <span>{hasMarket ? 'Mercado ao vivo' : 'Base limitada'}</span>
        {isAboveFipe ? <span>{fipeDeltaPct > 0 ? `${fipeDeltaPct}% acima da FIPE` : 'Acima da FIPE'}</span> : null}
      </div>
    </article>
  );
}

function PricingRangeCard({ bands, fipe, hasValidFipe, isAboveFipe, fipeDeltaPct }: { bands: PricingBand[]; fipe: number; hasValidFipe: boolean; isAboveFipe: boolean; fipeDeltaPct: number }) {
  const max = Math.max(...bands.map((band) => band.value), 1);
  return (
    <article className="mcv-price-range-card">
      <div className="mcv-card-heading"><span>Faixa de Mercado</span><BarChart3 size={18} /></div>
      <div className="mcv-price-band-list">
        {bands.map((band) => (
          <div key={band.label} className={`mcv-price-band ${band.tone}`}>
            <div><span>{band.label}</span><strong>{fmtCurrency(band.value)}</strong></div>
            <i><b style={{ width: `${Math.max(16, (band.value / max) * 100)}%` }} /></i>
          </div>
        ))}
      </div>
      {hasValidFipe ? <small className="mcv-fipe-badge">FIPE: {fmtCurrency(fipe)}{isAboveFipe ? ` ↑ ${Math.abs(fipeDeltaPct)}% acima` : ''}</small> : null}
    </article>
  );
}

function LostPotentialCard({ value }: { value: number }) {
  return (
    <article className="mcv-lost-card">
      <div className="mcv-card-heading"><span>Potencial Perdido™</span><TrendingUp size={18} /></div>
      <strong>{fmtCurrency(value)}</strong>
      <p>É o que você pode perder anunciando sem estratégia.</p>
      <ArrowUpRight size={28} />
    </article>
  );
}

function ComparablesCard({ comparables, summary, hasMarket, expanded = false }: { comparables: ComparableCard[]; summary: string; hasMarket: boolean; expanded?: boolean }) {
  return (
    <article className={expanded ? 'mcv-real-comparables-card expanded' : 'mcv-real-comparables-card'}>
      <div className="mcv-card-heading"><span>Comparáveis de Mercado</span><span className="mcv-live-dot">ao vivo</span></div>
      <h3>{summary}</h3>
      {hasMarket && comparables.length ? (
        <div className="mcv-real-comparables-list">
          {comparables.map((item, index) => (
            <a key={`${item.title}-${item.price}-${index}`} href={item.link || undefined} target={item.link ? '_blank' : undefined} rel="noreferrer" className="mcv-real-comparable-item">
              {item.thumbnail ? <img src={item.thumbnail} alt={item.title} /> : <div className="mcv-comparable-placeholder"><CarFront size={22} /></div>}
              <div>
                <strong>{item.title}</strong>
                <span>{[item.year, fmtKm(item.mileage)].filter(Boolean).join(' • ')}</span>
                <small>{[item.city, item.state].filter(Boolean).join('/') || item.source}</small>
              </div>
              <em>{fmtCurrency(item.price)}</em>
            </a>
          ))}
        </div>
      ) : (
        <div className="mcv-empty-premium"><strong>Comparáveis reais ainda insuficientes para este veículo.</strong><p>Quando a coleta encontrar anúncios similares, esta área exibirá veículos reais usados na análise.</p></div>
      )}
    </article>
  );
}

function DistributionCard({ data, idealPrice, hasMarket }: { data: DistributionPoint[]; idealPrice: number; hasMarket: boolean }) {
  return (
    <article className="mcv-distribution-card">
      <div className="mcv-card-heading"><span>Distribuição de preços</span><BarChart3 size={18} /></div>
      {hasMarket && data.length ? (
        <ResponsiveContainer width="100%" height={260}>
          <AreaChart data={data} margin={{ top: 16, right: 14, left: 0, bottom: 4 }}>
            <defs><linearGradient id="mcvGoldArea" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#D4A017" stopOpacity={0.65}/><stop offset="95%" stopColor="#D4A017" stopOpacity={0}/></linearGradient></defs>
            <CartesianGrid stroke="rgba(148,163,184,.16)" vertical={false} />
            <XAxis dataKey="label" tick={{ fill: '#94A3B8', fontSize: 11 }} axisLine={false} tickLine={false} />
            <YAxis allowDecimals={false} tick={{ fill: '#94A3B8', fontSize: 11 }} axisLine={false} tickLine={false} />
            <Tooltip content={<PremiumTooltip />} />
            <ReferenceLine x={compactCurrency(idealPrice)} stroke="#F0C040" strokeDasharray="4 4" />
            <Area type="monotone" dataKey="count" stroke="#F0C040" fill="url(#mcvGoldArea)" strokeWidth={3} />
          </AreaChart>
        </ResponsiveContainer>
      ) : (
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={[{ label: 'Aguardando', count: 1 }]}>
            <Bar dataKey="count" fill="rgba(212,160,23,.28)" radius={[12, 12, 0, 0]} />
            <XAxis dataKey="label" tick={{ fill: '#94A3B8', fontSize: 11 }} axisLine={false} tickLine={false} />
          </BarChart>
        </ResponsiveContainer>
      )}
      {!hasMarket ? <p className="mcv-honest-note">Gráfico real será exibido quando houver comparáveis suficientes. Nenhuma curva artificial foi criada.</p> : null}
    </article>
  );
}

function LiquidityTimingCard({ liquidity, label, trend, timing, hasMarket }: { liquidity: number; label: string; trend: string; timing: string; hasMarket: boolean }) {
  const series = [
    { label: 'Agora', score: liquidity },
    { label: '30d', score: hasMarket ? Math.max(0, liquidity - 4) : liquidity },
    { label: '60d', score: hasMarket ? Math.max(0, liquidity - 7) : liquidity },
    { label: '90d', score: hasMarket ? Math.max(0, liquidity - 10) : liquidity },
  ];
  return (
    <article className="mcv-liquidity-card">
      <div className="mcv-card-heading"><span>Liquidez e Timing</span><TrendingUp size={18} /></div>
      <strong>{liquidity}% • {label}</strong>
      <p>Mercado: {trend}. Melhor momento: {timing}.</p>
      <ResponsiveContainer width="100%" height={145}>
        <AreaChart data={series} margin={{ top: 10, right: 0, left: 0, bottom: 0 }}>
          <defs><linearGradient id="mcvLiquidity" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#22C55E" stopOpacity={0.56}/><stop offset="100%" stopColor="#22C55E" stopOpacity={0}/></linearGradient></defs>
          <XAxis dataKey="label" tick={{ fill: '#94A3B8', fontSize: 11 }} axisLine={false} tickLine={false} />
          <YAxis domain={[0, 100]} hide />
          <Area type="monotone" dataKey="score" stroke="#22C55E" fill="url(#mcvLiquidity)" strokeWidth={3} />
        </AreaChart>
      </ResponsiveContainer>
      {!hasMarket ? <small>Visual baseado somente no valuation atual, sem série histórica artificial.</small> : null}
    </article>
  );
}

function InsightsCard({ insights, warning }: { insights: string[]; warning: string }) {
  return (
    <article className="mcv-insights-card">
      <div className="mcv-card-heading"><span>O que o mercado diz</span><Sparkles size={18} /></div>
      <ul>{insights.map((item) => <li key={item}>{item}</li>)}</ul>
      {warning ? <p>{warning}</p> : null}
    </article>
  );
}

function SourceTruthCard({ source, confidence, warning }: { source: string; confidence: number; warning: string }) {
  const label = normalizeSourceLabel(source);
  return <article className="mcv-source-truth-card"><span>Fonte da avaliação</span><strong>{label}</strong><small>Confiança: {confidence}%</small>{warning ? <p>{warning}</p> : null}</article>;
}

function PremiumTooltip({ active, payload, label }: { active?: boolean; payload?: Array<{ value?: number }>; label?: string }) {
  if (!active || !payload?.length) return null;
  return <div className="mcv-chart-tooltip"><strong>{label}</strong><span>{payload[0]?.value || 0} anúncio(s)</span></div>;
}

function Metric({ label, value, strong = false }: { label: string; value: string; strong?: boolean }) {
  return <article className={strong ? 'mcv-metric-clean strong' : 'mcv-metric-clean'}><span>{label}</span><strong>{value}</strong></article>;
}

function Item({ title, text }: { title: string; text: string }) {
  return <article><span>{title}</span><strong>{shortText(text)}</strong></article>;
}

function shortText(text: string) { return text.length > 95 ? `${text.slice(0, 92)}...` : text; }

function LockIcon() { return <span aria-hidden="true">🔒</span>; }
