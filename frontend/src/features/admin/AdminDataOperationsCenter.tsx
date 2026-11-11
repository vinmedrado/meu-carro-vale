import { useEffect, useState } from 'react';
import { fetchAdminDataOperationsStatus, type AdminDataOperationsStatus } from '../../lib/api';

export function AdminDataOperationsCenter({ token }: { token: string }) {
  const [data, setData] = useState<AdminDataOperationsStatus | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  async function refresh() {
    setLoading(true);
    setError('');
    try { setData(await fetchAdminDataOperationsStatus(token)); }
    catch (err) { setError(err instanceof Error ? err.message : 'Falha ao consultar operações.'); }
    finally { setLoading(false); }
  }
  useEffect(() => { void refresh(); }, [token]);

  return <section className="mcv-muted-panel rounded-2xl p-5" aria-label="Operações internas de dados">
    <div className="flex items-center justify-between gap-4">
      <div><h2 className="text-lg font-semibold">Operações de Dados</h2>
        <p className="text-sm">Estado das integrações, sincronização FIPE e cache.</p></div>
      <button type="button" onClick={() => void refresh()} disabled={loading} className="admin-select px-3 py-2">Atualizar</button>
    </div>
    {loading && <p role="status">Carregando operações…</p>}
    {error && <p role="alert">{error}</p>}
    {data && !loading && <>
      <dl className="mt-4 grid gap-4 md:grid-cols-3">
        <div><dt>Saúde</dt><dd className="font-semibold">{data.health}</dd></div>
        <div><dt>FIPE</dt><dd className="font-semibold">{data.fipe.status}</dd></div>
        <div><dt>Cache</dt><dd className="font-semibold">{data.cache.status} · {data.cache.entries} itens</dd></div>
      </dl>
      {data.alerts.length > 0 && <div className="mt-4"><h3 className="font-semibold">Alertas</h3><ul>{data.alerts.map((alert, i) => <li key={i}>{alert}</li>)}</ul></div>}
    </>}
  </section>;
}
