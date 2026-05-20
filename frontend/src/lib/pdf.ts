import type { ValuationResult } from "../types";
import { fmtCurrency } from "./format";
import { getRecommendedTopPrice } from "./valuationAccessors";

function esc(value: unknown) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function row(label: string, value: string, note = "") {
  return `<tr><th>${esc(label)}</th><td>${esc(value)}</td><td>${esc(note)}</td></tr>`;
}

function compactComparableRows(result: ValuationResult) {
  const vehicleTitle = `${result.vehicle.brand} ${result.vehicle.model}`;
  const v = result.valuation;
  const fallback = [
    { title: vehicleTitle, price: v.market_reference, year: result.vehicle.year, mileage: result.vehicle.km || 82000, city: result.vehicle.city || 'São Paulo', state: result.vehicle.state || 'SP', source: 'Base regional', similarity_score: v.average_similarity_score || 91 },
  ];
  const comparables = v.comparables?.length ? v.comparables : fallback;
  return comparables.slice(0, 8).map((item) => `
    <tr>
      <td>${esc(item.title)}</td>
      <td>${esc(item.year)}</td>
      <td>${esc(Number(item.mileage || 0).toLocaleString('pt-BR'))} km</td>
      <td>${esc(item.city)}/${esc(item.state)}</td>
      <td>${esc(fmtCurrency(item.price))}</td>
      <td>${esc(item.source || 'Mercado')}</td>
      <td>${esc(item.similarity_score)}/100</td>
    </tr>`).join('');
}

function buildPrintDocument(result: ValuationResult) {
  const v = result.valuation;
  const vehicle = `${result.vehicle.brand} ${result.vehicle.model} ${result.vehicle.version}`;
  const generatedAt = new Date().toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' });
  const recommendedTop = getRecommendedTopPrice(v);
  const offer = Math.round((v.ideal_price * 0.81) / 100) * 100;
  const negotiationGap = Math.max(0, v.ideal_price - offer);
  const strategy = v.selling_strategy || {};
  const positioning = v.price_positioning || {};
  const marketInsights = v.market_insights || {};
  const buyerInsights = v.buyer_behavior_insights || v.buyer_behavior?.buyer_behavior_insights || [];
  const safeRange = v.safe_price_range || strategy.safe_price_range || v.negotiation_range || [];
  const marketBullets = v.market_insight_bullets || marketInsights.market_insight_bullets || [];
  const saleDecision = v.selling_decision || {};
  const listingPrice = v.listing_price || saleDecision.listing_price || v.recommended_listing_price || strategy.recommended_listing_price || v.ideal_price;
  const closeMin = v.ideal_close_range_min || saleDecision.ideal_close_range_min || safeRange[0] || v.negotiation_floor || v.quick_sale_price;
  const closeMax = v.ideal_close_range_max || saleDecision.ideal_close_range_max || safeRange[1] || v.negotiation_ceiling || recommendedTop;
  const minimumRecommended = v.minimum_recommended_price || saleDecision.minimum_recommended_price || v.quick_sale_price;
  const resistancePrice = v.resistance_price || saleDecision.resistance_price || v.probable_ceiling || v.negotiation_ceiling || recommendedTop;
  const defenseArguments = v.price_defense_arguments || saleDecision.price_defense_arguments || [];

  return `<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8" />
<title>Laudo Meu Carro Vale - ${esc(vehicle)}</title>
<style>
  :root{--bg:#F7F6F2;--paper:#fff;--ink:#161616;--muted:#5F6368;--line:#E5E1D8;--green:#1F6F4A;--gold:#B88A44;--danger:#B54732}
  *{box-sizing:border-box} body{margin:0;background:var(--bg);color:var(--ink);font:12px/1.45 Inter,Arial,sans-serif}.page{width:210mm;min-height:297mm;margin:0 auto;background:var(--paper);padding:18mm;position:relative}.brand{display:flex;justify-content:space-between;gap:18px;border-bottom:1px solid var(--line);padding-bottom:14px}.seal{border:1px solid var(--line);border-radius:999px;padding:6px 10px;color:var(--muted);font-size:11px}.kicker{color:var(--green);font-size:10px;font-weight:800;letter-spacing:.11em;text-transform:uppercase}h1{font-size:26px;line-height:1.1;margin:8px 0 6px;letter-spacing:-.03em}h2{font-size:15px;margin:0 0 10px}p{margin:0;color:var(--muted)}.meta{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}.meta span{border:1px solid var(--line);border-radius:99px;padding:5px 8px;color:var(--muted)}.range{margin:20px 0 16px;padding:14px;border:1px solid var(--line);border-radius:14px;background:#FAF9F6}.bar{height:8px;border-radius:99px;background:linear-gradient(90deg,var(--green),var(--gold));margin:12px 0}.metrics{display:grid;grid-template-columns:repeat(4,1fr);gap:8px}.metric{border:1px solid var(--line);border-radius:10px;padding:10px;background:#fff}.metric small{display:block;color:var(--muted);font-weight:700}.metric strong{display:block;margin-top:4px;font-size:17px}.metric.green strong{color:var(--green)}.metric.gold strong{color:var(--gold)}.section{margin-top:16px;padding-top:14px;border-top:1px solid var(--line)}table{width:100%;border-collapse:collapse}th{color:var(--muted);text-align:left;font-size:10px;text-transform:uppercase;letter-spacing:.08em}td,th{border-bottom:1px solid var(--line);padding:8px 6px;vertical-align:top}td{font-size:11px}.two{display:grid;grid-template-columns:1fr 1fr;gap:12px}.note{border:1px solid var(--line);border-radius:12px;padding:10px;background:#FAF9F6;color:var(--muted)}footer{position:absolute;left:18mm;right:18mm;bottom:12mm;border-top:1px solid var(--line);padding-top:8px;color:var(--muted);display:flex;justify-content:space-between;font-size:10px}@media print{body{background:#fff}.page{margin:0;box-shadow:none}}
</style>
</head>
<body>
<main class="page">
  <header class="brand">
    <div><div class="kicker">Laudo Meu Carro Vale</div><h1>${esc(vehicle)}</h1><p>${esc(result.vehicle.year || '2013')} · ${esc(Number(result.vehicle.km || 82000).toLocaleString('pt-BR'))} km · ${esc(result.vehicle.city || 'São Paulo')}/${esc(result.vehicle.state || 'SP')} · gerado em ${esc(generatedAt)}</p></div>
    <div class="seal">Documento executivo</div>
  </header>

  <section class="range">
    <div class="kicker">Faixa recomendada</div>
    <div class="bar"></div>
    <div class="metrics">
      <div class="metric"><small>Venda rápida</small><strong>${esc(fmtCurrency(v.quick_sale_price))}</strong></div>
      <div class="metric green"><small>Valor indicado</small><strong>${esc(fmtCurrency(v.ideal_price))}</strong></div>
      <div class="metric gold"><small>Faixa superior</small><strong>${esc(fmtCurrency(recommendedTop))}</strong></div>
      <div class="metric"><small>FIPE</small><strong>${esc(fmtCurrency(v.fipe_real || v.fipe_simulated))}</strong></div>
    </div>
  </section>

  <section class="section two">
    <div><div class="kicker">Resumo executivo</div><h2>Leitura comercial</h2><p>${esc(v.executive_market_insight_v2 || v.executive_market_insight || result.insights?.summary || 'A análise combina referência FIPE, amostra de mercado e características do veículo para apoiar uma negociação mais segura.')}</p></div>
    <div><div class="kicker">Negociação</div><h2>Potencial estimado</h2><p>Preço inicial recomendado: <strong>${esc(fmtCurrency(v.recommended_listing_price || strategy.recommended_listing_price || v.ideal_price))}</strong>. Faixa segura: ${esc(fmtCurrency(safeRange[0] || v.quick_sale_price))} a ${esc(fmtCurrency(safeRange[1] || recommendedTop))}. Uma oferta apressada pode reduzir sua margem em até <strong>${esc(fmtCurrency(negotiationGap))}</strong>.</p></div>
  </section>


  <section class="section">
    <div class="kicker">Estratégia de Venda</div><h2>Orientação para anunciar e negociar</h2>
    <table><tbody>
      ${row('Preço para anunciar', fmtCurrency(listingPrice), saleDecision.psychological_price_note || v.psychological_price_note || 'Preço com leitura comercial para anúncio')}
      ${row('Faixa ideal para fechar', `${fmtCurrency(closeMin)} a ${fmtCurrency(closeMax)}`, 'Intervalo recomendado para aceitar proposta')}
      ${row('Evite aceitar abaixo de', fmtCurrency(minimumRecommended), 'Ponto mínimo para preservar margem')}
      ${row('Teto com baixa liquidez', fmtCurrency(resistancePrice), 'Acima disso, há maior risco de resistência')}
      ${row('Risco de ficar parado', String(v.stuck_risk_level || saleDecision.stuck_risk_level || 'Moderado'), v.stuck_risk_reason || saleDecision.stuck_risk_reason || '')}
      ${row('Quando revisar preço', `${v.review_price_after_days || saleDecision.review_price_after_days || 10} dias`, `Se houver baixa procura, reduzir ${v.suggested_price_cut_percent || saleDecision.suggested_price_cut_percent || 2}% a 3%`)}
    </tbody></table>
    <div class="note" style="margin-top:10px"><strong>Resumo para o vendedor:</strong> ${esc(v.seller_summary || saleDecision.seller_summary || result.insights?.negotiation_recommendation)}</div>
  </section>

  <section class="section">
    <div class="kicker">Defesa do preço</div><h2>Argumentos para negociação</h2>
    <table><tbody>${(
  defenseArguments.length
    ? defenseArguments
    : (result.insights?.strengths || [
        'Preço alinhado ao mercado',
        'Boa liquidez regional',
        'Faixa de negociação clara',
      ])
)
  .slice(0, 5)
  .map((item, index) =>
    row(`Argumento ${index + 1}`, String(item), 'Use em conversas com compradores')
  )
  .join('')}</tbody></table>
  </section>

  <section class="section">
    <div class="kicker">Comparáveis usados</div><h2>Amostra de mercado</h2>
    <table><thead><tr><th>Veículo</th><th>Ano</th><th>Km</th><th>Praça</th><th>Preço</th><th>Fonte</th><th>Aderência</th></tr></thead><tbody>${compactComparableRows(result)}</tbody></table>
  </section>

  <section class="section two">
    <div class="note"><div class="kicker">Liquidez e pressão</div><h2>${esc(v.market_temperature_label || v.liquidity_label || 'Liquidez em análise')}</h2><p>${esc(v.estimated_market_resistance || v.liquidity_explanation || 'A liquidez considera oferta, procura, praça, faixa de valor e perfil do veículo.')}</p></div>
    <div class="note"><div class="kicker">Comportamento comprador</div><h2>${esc(v.buyer_price_sensitivity || v.buyer_behavior?.buyer_price_sensitivity || 'sensibilidade em análise')}</h2><p>${esc(buyerInsights[0] || result.insights?.negotiation_recommendation || 'Defenda o valor com base em histórico, conservação, quilometragem e comparáveis semelhantes.')}</p></div>
  </section>

  <section class="section">
    <div class="kicker">Inteligência comercial</div><h2>Leitura de venda</h2>
    <table><tbody>
      ${row('Temperatura de mercado', String(v.market_temperature_label || v.market_temperature || 'Estável'), marketInsights.market_thesis || '')}
      ${row('Posição frente aos comparáveis', `${v.market_position_percentile || positioning.market_position_percentile || 50}%`, v.competitiveness_level || positioning.competitiveness_level || 'competitivo')}
      ${row('Probabilidade de venda', `${v.sale_probability || 0}/100`, v.estimated_market_resistance || 'resistência em análise')}
      ${row('Ajuste recomendado', String(v.recommended_adjustment || strategy.recommended_adjustment || 'acompanhar resposta dos contatos'), marketBullets[0] || '')}
    </tbody></table>
  </section>

  <section class="section">
    <div class="kicker">Metodologia</div><h2>Critérios aplicados</h2>
    <table><tbody>
      ${row('FIPE', fmtCurrency(v.fipe_real || v.fipe_simulated), 'Piso técnico de referência')}
      ${row('Mercado observado', fmtCurrency(v.market_reference), 'Preço médio dos comparáveis')}
      ${row('Amostra', `${v.comparables_used || v.comparable_count || 0} comparáveis`, v.regional_scope || `${result.vehicle.city}/${result.vehicle.state}`)}
      ${row('Confiança da análise', `${v.confidence_score || 88}/100`, v.confidence_label || 'Amostra consistente')}
    </tbody></table>
  </section>

  <footer><span>Meu Carro Vale · valuation automotivo profissional</span><span>Use este laudo como apoio, não como garantia de venda.</span></footer>
</main>
<script>window.addEventListener('load',()=>setTimeout(()=>window.print(),250));</script>
</body>
</html>`;
}

export function exportValuationPdf(result: ValuationResult) {
  const html = buildPrintDocument(result);

  const blob = new Blob([html], { type: 'text/html;charset=utf-8' });
  const url = URL.createObjectURL(blob);

  const link = document.createElement('a');
  link.href = url;
  link.download = `laudo-meu-carro-vale-${Date.now()}.html`;

  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);

  URL.revokeObjectURL(url);
}