import { useEffect, useState } from 'react';
import { API_URL } from '../../lib/api';
import { fmtCurrency } from '../../lib/format';

type Panel = { plano_atual: string; laudos_usados_mes: number; limite_laudos: number; laudos_restantes: number; total_laudos: number; total_veiculos: number; modo: string };
type Report = { id: number; titulo: string; data: string; valor_recomendado: number; liquidez: string; confianca: string; status: string };
type Vehicle = { id: number; veiculo: string; ano: number; km: number; cidade: string; estado: string };
async function getJson<T>(token: string, path: string): Promise<T> { const res = await fetch(`${API_URL}${path}`, { headers: { Authorization: `Bearer ${token}` } }); if (!res.ok) throw new Error('Não foi possível carregar os dados da conta'); return res.json(); }
export function SaasDashboard({ token }: { token: string }) {
  const [panel, setPanel] = useState<Panel | null>(null);
  const [reports, setReports] = useState<Report[]>([]);
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  useEffect(() => { Promise.all([getJson<Panel>(token, '/api/saas/meu-painel'), getJson<Report[]>(token, '/api/saas/meus-laudos'), getJson<Vehicle[]>(token, '/api/saas/meus-veiculos')]).then(([p, r, v]) => { setPanel(p); setReports(r); setVehicles(v); }).catch(console.error); }, [token]);
  return (
    <section className="mcv-saas-area" id="meus-laudos">
      <div className="mcv-saas-summary">
        <div><span>Plano atual</span><strong>{panel?.plano_atual || 'Carregando'}</strong><small>{panel?.modo || 'Conta real'}</small></div>
        <div><span>Laudos no mês</span><strong>{panel ? `${panel.laudos_usados_mes}/${panel.limite_laudos}` : '--'}</strong><small>{panel?.laudos_restantes ?? '--'} restantes</small></div>
        <div><span>Veículos avaliados</span><strong>{panel?.total_veiculos ?? '--'}</strong><small>histórico do espaço</small></div>
        <div><span>Laudos salvos</span><strong>{panel?.total_laudos ?? '--'}</strong><small>com isolamento por conta</small></div>
      </div>
      <div className="mcv-saas-grid">
        <article className="mcv-saas-table-card"><header><h2>Meus Laudos</h2><p>Histórico das análises geradas pela sua conta.</p></header><div className="mcv-table-wrap"><table><thead><tr><th>Laudo</th><th>Valor</th><th>Liquidez</th><th>Confiança</th><th>Status</th></tr></thead><tbody>{reports.slice(0, 6).map((r) => <tr key={r.id}><td>{r.titulo}<small>{new Date(r.data).toLocaleDateString('pt-BR')}</small></td><td>{fmtCurrency(r.valor_recomendado || 0)}</td><td>{r.liquidez}</td><td>{r.confianca}</td><td>{r.status}</td></tr>)}</tbody></table></div></article>
        <article className="mcv-saas-table-card"><header><h2>Meus Veículos</h2><p>Veículos avaliados e disponíveis para nova análise.</p></header><div className="mcv-table-wrap"><table><thead><tr><th>Veículo</th><th>Ano</th><th>Km</th><th>Região</th></tr></thead><tbody>{vehicles.slice(0, 6).map((v) => <tr key={v.id}><td>{v.veiculo}</td><td>{v.ano}</td><td>{v.km.toLocaleString('pt-BR')}</td><td>{v.cidade}/{v.estado}</td></tr>)}</tbody></table></div></article>
      </div>
    </section>
  );
}
