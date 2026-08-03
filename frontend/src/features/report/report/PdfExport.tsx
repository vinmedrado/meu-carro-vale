import jsPDF from 'jspdf';
import type { ValuationResult } from '../../../types';
import { fmtCurrency } from '../../../lib/format';

const PAGE_WIDTH = 210;
const PAGE_HEIGHT = 297;
const MARGIN = 14;
const GOLD = '#D8A83F';
const GOLD_LIGHT = '#B8871D';
const BG = '#F5F7F8';
const SURFACE = '#FFFFFF';
const ELEVATED = '#FFFFFF';
const BORDER = '#E4E7EC';
const TEXT = '#101828';
const MUTED = '#667085';
const GREEN = '#166F52';
const RED = '#EF4444';

type PdfComparable = {
  title: string;
  price: number;
  year?: number | string | null;
  mileage?: number | string | null;
  source?: string;
  city?: string;
  state?: string;
  thumbnail?: string;
};

type PriceStats = {
  min: number;
  p25: number;
  median: number;
  p75: number;
  max: number;
};

type PdfViewModel = {
  vehicleName: string;
  vehicleYear: string;
  vehicleKm: string;
  vehicleLocation: string;
  generatedAt: string;
  generatedFileStamp: string;
  score: number;
  confidence: number;
  quickPrice: number;
  idealPrice: number;
  premiumPrice: number;
  fipePrice: number;
  hasValidFipe: boolean;
  sourceLabel: string;
  warning: string;
  comparableCount: number;
  comparables: PdfComparable[];
  stats: PriceStats | null;
  insights: string[];
  recommendations: string[];
  heroImageUrl: string;
};

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === 'object' ? (value as Record<string, unknown>) : {};
}

function asString(value: unknown, fallback = ''): string {
  return typeof value === 'string' && value.trim() ? value.trim() : fallback;
}

function asNumber(value: unknown, fallback = 0): number {
  const n = Number(value);
  return Number.isFinite(n) ? n : fallback;
}

function asPositive(value: unknown, fallback = 0): number {
  const n = Number(value);
  return Number.isFinite(n) && n > 0 ? n : fallback;
}

function normalizeComparableAnalysis(value: unknown): unknown[] {
  if (Array.isArray(value)) return value;
  if (value && typeof value === 'object') return [value];
  return [];
}

function normalizeSourceLabel(source: unknown): string {
  const value = String(source || '').trim().toLowerCase();
  if (['market_real', 'mercadolivre_api', 'mercadolivre', 'market_listings', 'ml_api'].includes(value)) return 'Dados reais de mercado';
  if (['fipe_local', 'cache_local'].includes(value)) return 'FIPE local';
  if (['fallback_estimado', 'unavailable', 'fallback'].includes(value)) return 'Estimativa';
  return value ? String(source) : 'Estimativa';
}

function formatKm(value: unknown): string {
  const n = Number(value);
  return Number.isFinite(n) && n > 0 ? `${Math.round(n).toLocaleString('pt-BR')} km` : 'KM não informado';
}

function safeCurrency(value: number): string {
  return Number.isFinite(value) && value > 0 ? fmtCurrency(Math.round(value)) : 'Não informado';
}

function clip(text: string, limit: number): string {
  if (text.length <= limit) return text;
  return `${text.slice(0, Math.max(0, limit - 1)).trim()}…`;
}

function normalizeComparable(item: unknown, index: number): PdfComparable | null {
  const record = asRecord(item);
  const price = asPositive(record.price, 0);
  const title = asString(record.title ?? record.vehicle_title ?? record.name ?? record.label, `Comparável ${index + 1}`);
  if (!price || !title) return null;
  return {
    title,
    price,
    year: (record.year ?? record.year_model ?? record.model_year) as number | string | null | undefined,
    mileage: (record.mileage ?? record.mileage_km ?? record.km) as number | string | null | undefined,
    source: asString(record.source, 'Mercado'),
    city: asString(record.city, ''),
    state: asString(record.state, ''),
    thumbnail: asString(record.thumbnail ?? record.image_url ?? record.imageUrl, ''),
  };
}

function percentile(sorted: number[], p: number): number {
  if (!sorted.length) return 0;
  const index = (sorted.length - 1) * p;
  const lower = Math.floor(index);
  const upper = Math.ceil(index);
  if (lower === upper) return sorted[lower];
  return sorted[lower] + (sorted[upper] - sorted[lower]) * (index - lower);
}

function buildStats(comparables: PdfComparable[], valuation: Record<string, unknown>): PriceStats | null {
  const dispersion = asRecord(valuation.price_dispersion);
  const explicitMedian = asPositive(dispersion.median ?? dispersion.p50, 0);
  if (explicitMedian) {
    return {
      min: asPositive(dispersion.min, explicitMedian),
      p25: asPositive(dispersion.p25, explicitMedian),
      median: explicitMedian,
      p75: asPositive(dispersion.p75, explicitMedian),
      max: asPositive(dispersion.max, explicitMedian),
    };
  }
  const prices = comparables.map((item) => item.price).filter((price) => price > 0).sort((a, b) => a - b);
  if (!prices.length) return null;
  return {
    min: prices[0],
    p25: percentile(prices, 0.25),
    median: percentile(prices, 0.5),
    p75: percentile(prices, 0.75),
    max: prices[prices.length - 1],
  };
}

function getInsights(result: ValuationResult, hasMarket: boolean, warning: string): string[] {
  const valuation = result.valuation;
  const customer = result.customer_valuation;
  const values = [
    ...(Array.isArray(customer?.valuation_insights) ? customer.valuation_insights : []),
    ...(Array.isArray(valuation.valuation_insights) ? valuation.valuation_insights : []),
    ...(Array.isArray(valuation.market_insight_bullets) ? valuation.market_insight_bullets : []),
    ...(Array.isArray(result.insights?.strengths) ? result.insights.strengths : []),
  ].filter((item): item is string => typeof item === 'string' && item.trim().length > 0);
  const fallback = hasMarket
    ? ['Preço recomendado calculado com base em anúncios reais disponíveis.', 'A faixa entre venda rápida e valor premium define sua margem de negociação.', 'Use os comparáveis para defender o preço com mais segurança.']
    : ['Comparáveis reais ainda insuficientes para este veículo.', warning || 'A análise usa a melhor referência disponível no momento.', 'Revise o preço quando novos anúncios semelhantes forem coletados.'];
  return (values.length ? values : fallback).slice(0, 4);
}

function getRecommendations(vm: Pick<PdfViewModel, 'quickPrice' | 'idealPrice' | 'premiumPrice' | 'comparableCount' | 'warning'>): string[] {
  const recs = [
    `Venda rápida: anunciar próximo de ${safeCurrency(vm.quickPrice)} para acelerar contatos.`,
    `Preço ideal: defender ${safeCurrency(vm.idealPrice)} como referência principal.`,
    `Valor premium: usar ${safeCurrency(vm.premiumPrice)} se o veículo estiver muito bem conservado e sem pressa para vender.`,
  ];
  if (vm.comparableCount <= 0) recs.push(vm.warning || 'Aguarde mais comparáveis antes de subir muito o preço.');
  return recs;
}

function buildViewModel(result: ValuationResult): PdfViewModel {
  const valuation = result.valuation;
  const customer = result.customer_valuation;
  const rawComparables = [
    ...(Array.isArray(valuation.comparables) ? valuation.comparables : []),
    ...(Array.isArray(customer?.comparables_preview) ? customer.comparables_preview : []),
    ...normalizeComparableAnalysis(valuation.comparable_analysis),
  ];
  const comparables = rawComparables
    .map((item, index) => normalizeComparable(item, index))
    .filter((item): item is PdfComparable => Boolean(item))
    .slice(0, 8);
  const fipePrice = asPositive(customer?.fipe_price ?? valuation.fipe_price ?? valuation.fipe_real ?? valuation.fipe_simulated, 0);
  const marketReference = asPositive(valuation.market_reference ?? customer?.market_price_estimate, fipePrice);
  const idealPrice = asPositive(customer?.recommended_price ?? valuation.recommended_price ?? valuation.ideal_price, marketReference);
  const quickPrice = asPositive(customer?.quick_sale_price ?? valuation.quick_sale_price, Math.round(idealPrice * 0.94));
  const premiumPrice = asPositive(customer?.premium_sale_price ?? valuation.premium_sale_price ?? valuation.recommended_top_price, Math.round(idealPrice * 1.06));
  const comparableCount = asNumber(customer?.comparable_count ?? valuation.comparable_count ?? valuation.comparables_used ?? valuation.comparables_count ?? comparables.length, comparables.length);
  const sourceLabel = normalizeSourceLabel(valuation.base_price_source ?? valuation.data_source ?? valuation.fipe_source ?? customer?.market_sources?.[0]);
  const isFallback = sourceLabel.toLowerCase().includes('estimativa');
  const warning = asString(valuation.warning ?? valuation.low_confidence_message, isFallback ? 'Estimativa calculada por fallback por ausência de dados suficientes.' : '');
  const generated = new Date();
  const vehicleName = `${result.vehicle.brand || ''} ${result.vehicle.model || ''}`.trim() || asString(customer?.vehicle_label ?? valuation.vehicle_label, 'Veículo avaliado');
  const heroImageUrl = asString(comparables.find((item) => item.thumbnail)?.thumbnail, '');
  const score = Math.max(0, Math.min(100, Math.round(asNumber(valuation.vehicle_score ?? valuation.attractiveness_score ?? customer?.liquidity_score ?? valuation.liquidity_score, 0))));
  const confidence = Math.max(0, Math.min(100, Math.round(asNumber(customer?.confidence_score ?? valuation.confidence_score, comparableCount > 0 ? 75 : 45))));
  const model: PdfViewModel = {
    vehicleName,
    vehicleYear: String(result.vehicle.year || 'Ano não informado'),
    vehicleKm: formatKm(result.vehicle.km),
    vehicleLocation: [result.vehicle.city, result.vehicle.state].filter(Boolean).join('/') || 'Localização não informada',
    generatedAt: generated.toLocaleDateString('pt-BR', { day: '2-digit', month: 'long', year: 'numeric' }),
    generatedFileStamp: generated.toISOString().slice(0, 10),
    score,
    confidence,
    quickPrice,
    idealPrice,
    premiumPrice,
    fipePrice,
    hasValidFipe: fipePrice > 0,
    sourceLabel,
    warning,
    comparableCount,
    comparables,
    stats: buildStats(comparables, valuation),
    insights: [],
    recommendations: [],
    heroImageUrl,
  };
  model.insights = getInsights(result, comparableCount > 0, warning);
  model.recommendations = getRecommendations(model);
  return model;
}

function setPage(doc: jsPDF): void {
  doc.setFillColor(BG);
  doc.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, 'F');
}

function addFooter(doc: jsPDF, page: number, generatedAt: string): void {
  doc.setDrawColor(BORDER);
  doc.line(MARGIN, PAGE_HEIGHT - 15, PAGE_WIDTH - MARGIN, PAGE_HEIGHT - 15);
  doc.setFont('helvetica', 'normal');
  doc.setFontSize(8);
  doc.setTextColor(MUTED);
  doc.text(`meucarrovale.com.br | Relatório gerado em ${generatedAt}`, MARGIN, PAGE_HEIGHT - 9);
  doc.text(`Página ${page}/4`, PAGE_WIDTH - MARGIN, PAGE_HEIGHT - 9, { align: 'right' });
}

function addBrand(doc: jsPDF, subtitle = 'Laudo Premium'): void {
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(13);
  doc.setTextColor(GOLD_LIGHT);
  doc.text('Meu Carro Vale', MARGIN, 18);
  doc.setFont('helvetica', 'normal');
  doc.setFontSize(8);
  doc.setTextColor(MUTED);
  doc.text(subtitle.toUpperCase(), MARGIN, 23);
}

function card(doc: jsPDF, x: number, y: number, w: number, h: number, title?: string): void {
  doc.setFillColor(SURFACE);
  doc.setDrawColor(BORDER);
  doc.roundedRect(x, y, w, h, 3, 3, 'FD');
  if (title) {
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(8);
    doc.setTextColor(GOLD_LIGHT);
    doc.text(title.toUpperCase(), x + 4, y + 7);
  }
}

function labelValue(doc: jsPDF, label: string, value: string, x: number, y: number, color = TEXT): void {
  doc.setFont('helvetica', 'normal');
  doc.setFontSize(8);
  doc.setTextColor(MUTED);
  doc.text(label, x, y);
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(13);
  doc.setTextColor(color);
  doc.text(value, x, y + 8);
}

function wrapped(doc: jsPDF, text: string, x: number, y: number, maxWidth: number, lineHeight = 5): number {
  const lines = doc.splitTextToSize(text, maxWidth) as string[];
  doc.text(lines, x, y);
  return y + lines.length * lineHeight;
}


async function loadImageDataUrl(url: string): Promise<string | null> {
  if (!url) return null;
  try {
    const response = await fetch(url, { mode: 'cors' });
    if (!response.ok) return null;
    const blob = await response.blob();
    return await new Promise((resolve) => {
      const reader = new FileReader();
      reader.onload = () => resolve(typeof reader.result === 'string' ? reader.result : null);
      reader.onerror = () => resolve(null);
      reader.readAsDataURL(blob);
    });
  } catch {
    return null;
  }
}

function page1(doc: jsPDF, vm: PdfViewModel, heroImageDataUrl: string | null): void {
  setPage(doc);
  addBrand(doc, 'Relatório inteligente de valuation automotivo');
  doc.setFillColor(ELEVATED);
  doc.roundedRect(MARGIN, 38, PAGE_WIDTH - MARGIN * 2, 95, 5, 5, 'F');
  doc.setDrawColor(GOLD);
  doc.setLineWidth(0.6);
  doc.roundedRect(MARGIN + 2, 40, PAGE_WIDTH - MARGIN * 2 - 4, 91, 4, 4, 'S');
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(TEXT);
  doc.setFontSize(28);
  wrapped(doc, vm.vehicleName, MARGIN + 10, 62, 120, 11);
  doc.setFont('helvetica', 'normal');
  doc.setFontSize(12);
  doc.setTextColor(MUTED);
  doc.text(`${vm.vehicleYear} • ${vm.vehicleKm} • ${vm.vehicleLocation}`, MARGIN + 10, 92);
  doc.setFontSize(10);
  doc.text(`Gerado em ${vm.generatedAt}`, MARGIN + 10, 103);
  doc.setFillColor(GOLD);
  doc.roundedRect(MARGIN + 10, 112, 62, 11, 5, 5, 'F');
  doc.setTextColor('#101828');
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(8);
  doc.text('RELATÓRIO PREMIUM', MARGIN + 16, 119);
  doc.setFillColor('#F2F4F7');
  doc.roundedRect(PAGE_WIDTH - MARGIN - 64, 50, 52, 52, 6, 6, 'F');
  if (heroImageDataUrl) {
    try {
      doc.addImage(heroImageDataUrl, 'JPEG', PAGE_WIDTH - MARGIN - 62, 52, 48, 48, undefined, 'FAST');
    } catch {
      doc.setFontSize(25);
      doc.setTextColor(GOLD_LIGHT);
      doc.text('MCV', PAGE_WIDTH - MARGIN - 54, 81);
    }
  } else {
    doc.setFontSize(25);
    doc.setTextColor(GOLD_LIGHT);
    doc.text('MCV', PAGE_WIDTH - MARGIN - 54, 81);
    doc.setFont('helvetica', 'normal');
    doc.setFontSize(7);
    doc.setTextColor(MUTED);
    doc.text('Imagem indisponível', PAGE_WIDTH - MARGIN - 58, 94);
  }
  card(doc, MARGIN, 150, PAGE_WIDTH - MARGIN * 2, 42, 'Resumo do valor');
  labelValue(doc, 'Preço ideal', safeCurrency(vm.idealPrice), MARGIN + 7, 165, GOLD_LIGHT);
  labelValue(doc, 'Venda rápida', safeCurrency(vm.quickPrice), MARGIN + 67, 165, TEXT);
  labelValue(doc, 'Valor premium', safeCurrency(vm.premiumPrice), MARGIN + 127, 165, GREEN);
  doc.setFont('helvetica', 'normal');
  doc.setFontSize(9);
  doc.setTextColor(MUTED);
  wrapped(doc, `Fonte: ${vm.sourceLabel}. ${vm.comparableCount > 0 ? `Baseado em ${vm.comparableCount} anúncios ativos e referências locais disponíveis.` : 'Comparáveis reais ainda insuficientes para este veículo.'}`, MARGIN, 210, PAGE_WIDTH - MARGIN * 2);
  addFooter(doc, 1, vm.generatedAt);
}

function page2(doc: jsPDF, vm: PdfViewModel): void {
  doc.addPage();
  setPage(doc);
  addBrand(doc, 'Resumo Executivo');
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(21);
  doc.setTextColor(TEXT);
  doc.text('Resumo executivo', MARGIN, 40);
  card(doc, MARGIN, 52, 82, 58, 'Índice Meu Carro Vale™');
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(34);
  doc.setTextColor(GOLD_LIGHT);
  doc.text(String(vm.score || vm.confidence), MARGIN + 34, 82, { align: 'center' });
  doc.setFontSize(9);
  doc.setTextColor(MUTED);
  doc.text('Pontuação consolidada do veículo', MARGIN + 7, 99);
  card(doc, MARGIN + 92, 52, 90, 58, 'Confiança');
  labelValue(doc, 'Score de confiança', `${vm.confidence}/100`, MARGIN + 99, 70, vm.confidence >= 70 ? GREEN : GOLD_LIGHT);
  doc.setFont('helvetica', 'normal');
  doc.setFontSize(8);
  doc.setTextColor(MUTED);
  wrapped(doc, `Fonte: ${vm.sourceLabel}`, MARGIN + 99, 91, 72);
  card(doc, MARGIN, 124, PAGE_WIDTH - MARGIN * 2, 48, 'Faixas de preço');
  labelValue(doc, 'Venda rápida', safeCurrency(vm.quickPrice), MARGIN + 7, 140);
  labelValue(doc, 'Preço ideal', safeCurrency(vm.idealPrice), MARGIN + 68, 140, GOLD_LIGHT);
  labelValue(doc, 'Valor premium', safeCurrency(vm.premiumPrice), MARGIN + 128, 140, GREEN);
  let sourceText = `Baseado em ${vm.comparableCount} anúncio(s) ativo(s)`;
  if (vm.hasValidFipe) sourceText += ` + FIPE local de ${safeCurrency(vm.fipePrice)}`;
  card(doc, MARGIN, 185, PAGE_WIDTH - MARGIN * 2, 42, 'Fonte dos dados');
  doc.setFont('helvetica', 'normal');
  doc.setFontSize(10);
  doc.setTextColor(TEXT);
  wrapped(doc, sourceText, MARGIN + 7, 200, PAGE_WIDTH - MARGIN * 2 - 14);
  if (vm.warning) {
    doc.setTextColor(GOLD_LIGHT);
    doc.setFontSize(9);
    wrapped(doc, vm.warning, MARGIN + 7, 216, PAGE_WIDTH - MARGIN * 2 - 14);
  }
  addFooter(doc, 2, vm.generatedAt);
}

function drawDistribution(doc: jsPDF, vm: PdfViewModel, x: number, y: number, w: number, h: number): void {
  const prices = vm.comparables.map((item) => item.price).filter((price) => price > 0);
  if (!prices.length) {
    doc.setFont('helvetica', 'normal');
    doc.setFontSize(10);
    doc.setTextColor(MUTED);
    wrapped(doc, 'Comparáveis reais ainda insuficientes para este veículo.', x + 6, y + 24, w - 12);
    return;
  }
  const max = Math.max(...prices);
  const bars = prices.slice(0, 7);
  bars.forEach((price, index) => {
    const barH = Math.max(5, (price / max) * (h - 20));
    const barW = (w - 20) / bars.length - 3;
    const bx = x + 8 + index * ((w - 20) / bars.length);
    const by = y + h - 8 - barH;
    doc.setFillColor(index % 2 === 0 ? GOLD : GOLD_LIGHT);
    doc.roundedRect(bx, by, barW, barH, 1.5, 1.5, 'F');
  });
  doc.setDrawColor(GREEN);
  const idealX = x + 8 + Math.min(1, vm.idealPrice / max) * (w - 22);
  doc.line(idealX, y + 12, idealX, y + h - 6);
  doc.setFontSize(7);
  doc.setTextColor(GREEN);
  doc.text('Preço ideal', idealX + 1, y + 10);
}

function page3(doc: jsPDF, vm: PdfViewModel): void {
  doc.addPage();
  setPage(doc);
  addBrand(doc, 'Análise de Mercado');
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(21);
  doc.setTextColor(TEXT);
  doc.text('Análise de mercado', MARGIN, 40);
  card(doc, MARGIN, 52, PAGE_WIDTH - MARGIN * 2, 62, 'Distribuição de preços');
  drawDistribution(doc, vm, MARGIN + 6, 62, PAGE_WIDTH - MARGIN * 2 - 12, 45);
  const statsY = 126;
  card(doc, MARGIN, statsY, PAGE_WIDTH - MARGIN * 2, 28, 'Medidas de mercado');
  if (vm.stats) {
    labelValue(doc, 'Mín.', safeCurrency(vm.stats.min), MARGIN + 6, statsY + 13);
    labelValue(doc, 'P25', safeCurrency(vm.stats.p25), MARGIN + 43, statsY + 13);
    labelValue(doc, 'Mediana', safeCurrency(vm.stats.median), MARGIN + 80, statsY + 13, GOLD_LIGHT);
    labelValue(doc, 'P75', safeCurrency(vm.stats.p75), MARGIN + 124, statsY + 13);
    labelValue(doc, 'Máx.', safeCurrency(vm.stats.max), MARGIN + 158, statsY + 13);
  } else {
    doc.setTextColor(MUTED);
    doc.setFontSize(9);
    doc.text('Sem amostra suficiente para mediana/P25/P75.', MARGIN + 6, statsY + 17);
  }
  card(doc, MARGIN, 168, PAGE_WIDTH - MARGIN * 2, 82, 'Anúncios similares');
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(8);
  doc.setTextColor(MUTED);
  doc.text('Título', MARGIN + 6, 181);
  doc.text('Ano', MARGIN + 86, 181);
  doc.text('KM', MARGIN + 108, 181);
  doc.text('Preço', MARGIN + 143, 181);
  doc.text('Fonte', MARGIN + 170, 181);
  doc.setDrawColor(BORDER);
  doc.line(MARGIN + 6, 184, PAGE_WIDTH - MARGIN - 6, 184);
  if (!vm.comparables.length) {
    doc.setFont('helvetica', 'normal');
    doc.setFontSize(9);
    doc.setTextColor(MUTED);
    doc.text('Comparáveis reais ainda insuficientes para este veículo.', MARGIN + 6, 196);
  } else {
    vm.comparables.slice(0, 6).forEach((item, index) => {
      const rowY = 194 + index * 9;
      doc.setFont('helvetica', 'normal');
      doc.setFontSize(7.5);
      doc.setTextColor(TEXT);
      doc.text(clip(item.title, 42), MARGIN + 6, rowY);
      doc.setTextColor(MUTED);
      doc.text(String(item.year || '-'), MARGIN + 86, rowY);
      doc.text(formatKm(item.mileage).replace(' km', ''), MARGIN + 108, rowY);
      doc.setTextColor(GOLD_LIGHT);
      doc.text(safeCurrency(item.price), MARGIN + 143, rowY);
      doc.setTextColor(MUTED);
      doc.text(clip(item.source || 'Mercado', 14), MARGIN + 170, rowY);
    });
  }
  addFooter(doc, 3, vm.generatedAt);
}

function page4(doc: jsPDF, vm: PdfViewModel): void {
  doc.addPage();
  setPage(doc);
  addBrand(doc, 'Estratégia de Venda');
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(21);
  doc.setTextColor(TEXT);
  doc.text('Estratégia de venda', MARGIN, 40);
  const scenarioW = (PAGE_WIDTH - MARGIN * 2 - 10) / 3;
  const scenarios = [
    ['Cenário 1', 'Venda rápida', vm.quickPrice, 'Para gerar mais contatos e vender em menos tempo.'],
    ['Cenário 2', 'Preço ideal', vm.idealPrice, 'Referência principal para anunciar e negociar.'],
    ['Cenário 3', 'Valor premium', vm.premiumPrice, 'Para veículos acima da média e sem pressa de venda.'],
  ] as const;
  scenarios.forEach((scenario, index) => {
    const x = MARGIN + index * (scenarioW + 5);
    card(doc, x, 56, scenarioW, 58, scenario[0]);
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(11);
    doc.setTextColor(TEXT);
    doc.text(scenario[1], x + 5, 72);
    doc.setFontSize(14);
    doc.setTextColor(index === 1 ? GOLD_LIGHT : index === 2 ? GREEN : TEXT);
    doc.text(safeCurrency(scenario[2]), x + 5, 86);
    doc.setFont('helvetica', 'normal');
    doc.setFontSize(8);
    doc.setTextColor(MUTED);
    wrapped(doc, scenario[3], x + 5, 99, scenarioW - 10, 4);
  });
  card(doc, MARGIN, 132, PAGE_WIDTH - MARGIN * 2, 54, 'Insights principais');
  doc.setFont('helvetica', 'normal');
  doc.setFontSize(9);
  doc.setTextColor(TEXT);
  let y = 146;
  vm.insights.slice(0, 4).forEach((item) => {
    doc.setTextColor(GOLD_LIGHT);
    doc.text('•', MARGIN + 6, y);
    doc.setTextColor(TEXT);
    y = wrapped(doc, item, MARGIN + 11, y, PAGE_WIDTH - MARGIN * 2 - 18, 5) + 2;
  });
  card(doc, MARGIN, 202, PAGE_WIDTH - MARGIN * 2, 45, 'Recomendações de anúncio');
  doc.setFontSize(8.5);
  doc.setTextColor(TEXT);
  y = 216;
  vm.recommendations.slice(0, 4).forEach((item) => {
    doc.setTextColor(GREEN);
    doc.text('✓', MARGIN + 6, y);
    doc.setTextColor(TEXT);
    y = wrapped(doc, item, MARGIN + 12, y, PAGE_WIDTH - MARGIN * 2 - 18, 4.5) + 1;
  });
  addFooter(doc, 4, vm.generatedAt);
}

export async function exportReportPdf(result: ValuationResult): Promise<void> {
  const vm = buildViewModel(result);
  const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4', compress: true });
  const heroImageDataUrl = await loadImageDataUrl(vm.heroImageUrl);
  page1(doc, vm, heroImageDataUrl);
  page2(doc, vm);
  page3(doc, vm);
  page4(doc, vm);
  const safeName = vm.vehicleName.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '') || 'veiculo';
  doc.save(`laudo-meu-carro-vale-${safeName}-${vm.generatedFileStamp}.pdf`);
}
