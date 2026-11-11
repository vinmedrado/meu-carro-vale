import { useEffect, useState } from 'react';
import { fetchMarketImportQuality, type MarketImportQualitySummary } from '../../lib/api';

export function MarketDataQualityPanel({ token }: { token: string }) {
  const [summary, setSummary] = useState<MarketImportQualitySummary | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  async function refresh() {
    setLoading(true);
    setError('');
    try { setSummary(await fetchMarketImportQuality(token)); }
    catch (err) { setError(err instanceof Error ? err.message : 'Não foi possível consultar os dados.'); }
    finally { setLoading(false); }
  }
  useEffect(() => { void refresh(); }, [token]);

  return <section className="mcv-muted-panel rounded-2xl p-5" aria-label="Qualidade dos dados de mercado">
    <div className="flex items-center justify-between gap-4">
      <div><h2 className="text-lg font-semibold">Qualidade dos Dados de Mercado</h2>
        <p className="text-sm">Auditoria das importações e fontes utilizadas nas análises.</p></div>
      <button type="button" onClick={() => void refresh()} disabled={loading} className="admin-select px-3 py-2">Atualizar</button>
    </div>
    {loading && <p role="status">Consultando indicadores…</p>}
    {error && <p role="alert">{error}</p>}
    {summary && !loading && <div className="mt-4 grid gap-3 md:grid-cols-3">
      <div><small>Qualidade</small><strong className="block text-xl">{summary.quality_score ?? 0}</strong><span>{summary.quality_label}</span></div>
      <div><small>Importações</small><strong className="block text-xl">{summary.total_imports ?? 0}</strong></div>
      <div><small>Registros válidos</small><strong className="block text-xl">{summary.total_valid ?? 0}</strong></div>
      <div className="md:col-span-3"><h3 className="font-semibold">Fontes</h3>
        {summary.by_source.length === 0 ? <p>Nenhuma importação registrada.</p> :
          <ul>{summary.by_source.map((item) => <li key={item.source}>{item.source}: {item.valid ?? item.total_valid ?? 0} válidos</li>)}</ul>}
      </div>
    </div>}
  </section>;
}
