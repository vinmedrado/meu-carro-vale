import type { ValuationResult } from '../../types';

export function ValuationIntelligence({ result, compact = false }: { result: ValuationResult; compact?: boolean }) {
  const market = result.valuation;
  const customer = result.customer_valuation;
  const confidence = customer?.confidence_score ?? market.confidence_score;
  const summary = customer?.human_summary ?? market.executive_market_insight ?? market.methodology_note;
  const sources = customer?.market_sources ?? market.sources ?? [];

  return <section className="mcv-muted-panel rounded-2xl p-5" aria-label="Inteligência de avaliação">
    <h3 className="text-lg font-semibold">Inteligência de avaliação</h3>
    {summary && <p className="mt-2 text-sm">{summary}</p>}
    <dl className="mt-3 grid gap-3 sm:grid-cols-2">
      <div><dt>Confiança</dt><dd>{typeof confidence === 'number' ? `${Math.round(confidence)}/100` : 'Não informada'}</dd></div>
      <div><dt>Comparáveis</dt><dd>{customer?.comparable_count ?? market.comparables_used ?? market.comparable_count ?? 0}</dd></div>
    </dl>
    {!compact && sources.length > 0 && <p className="mt-2 text-xs">Fontes: {sources.join(', ')}</p>}
  </section>;
}
