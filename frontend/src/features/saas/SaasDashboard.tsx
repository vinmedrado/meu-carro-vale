import { useEffect, useState } from 'react';
import { API_URL, PORTFOLIO_MODE } from '../../lib/api';
import { fmtCurrency } from '../../lib/format';

type Panel = { plano_atual: string; plan_id?: string; features?: Record<string, boolean>; laudos_usados_mes: number; limite_laudos: number; laudos_restantes: number; total_laudos: number; total_veiculos: number; modo: string };
type Report = { id: number; titulo: string; data: string; valor_recomendado: number; liquidez: string; confianca: string; status: string };
type ReportsResponse = Report[] | { locked?: boolean; message?: string; items?: Report[] };
type Vehicle = { id: number; veiculo: string; ano: number; km: number; cidade: string; estado: string };
function scoreFromReports(reports: Report[]) {
  if (!reports.length) return { liquidity: 0, confidence: 0, premium: 'Aguardando laudos' };
  const confidence = Math.round(reports.reduce((acc, r) => acc + (Number(String(r.confianca).replace(/\D/g, '')) || 78), 0) / reports.length);
  const strongLiquidity = reports.filter((r) => /boa|alta|rápida|aquecid/i.test(r.liquidez || '')).length;
  const liquidity = Math.round(62 + (strongLiquidity / reports.length) * 30);
  return { liquidity, confidence, premium: liquidity >= 78 ? 'Carteira com boa liquidez' : 'Carteira em calibração' };
}
function PremiumSkeleton() { return <div className="mcv-ai-skeleton"><div className="mcv-shimmer big" /><div className="mcv-shimmer mid" /><div className="mcv-shimmer" /></div>; }
function EmptyState({ text }: { text: string }) { return <div className="mcv-empty-premium">{text}</div>; }
async function getJson<T>(token: string, path: string): Promise<T> { const res = await fetch(`${API_URL}${path}`, { headers: { Authorization: `Bearer ${token}` } }); if (!res.ok) throw new Error('Não foi possível carregar os dados da conta'); return res.json(); }
export function SaasDashboard({ token }: { token: string }) {
  const [panel, setPanel] = useState<Panel | null>(null);
  const [reports, setReports] = useState<Report[]>([]);
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  useEffect(() => {
    if (PORTFOLIO_MODE) {
      setPanel({ plano_atual: 'Demo Portfolio', plan_id: 'pro', features: { pdf: true, history: true }, laudos_usados_mes: 1, limite_laudos: 20, laudos_restantes: 19, total_laudos: 1, total_veiculos: 1, modo: 'Experiência demonstrativa' });
      setReports([{ id: 1, titulo: 'Laudo Meu Carro Vale - Chevrolet Agile', data: new Date().toISOString(), valor_recomendado: 38900, liquidez: 'Alta', confianca: '82/100', status: 'gerado' }]);
      setVehicles([{ id: 1, veiculo: 'Chevrolet Agile LTZ 1.4 Flex', ano: 2013, km: 82000, cidade: 'São Paulo', estado: 'SP' }]);
      return;
    }
    Promise.all([getJson<Panel>(token, '/api/saas/meu-painel'), getJson<ReportsResponse>(token, '/api/saas/meus-laudos'), getJson<Vehicle[]>(token, '/api/saas/meus-veiculos')]).then(([p, r, v]) => { setPanel(p); setReports(Array.isArray(r) ? r : (r.items || [])); setVehicles(v); }).catch(console.error);
  }, [token]);
  const intelligence = scoreFromReports(reports);
  return (
    <section className="mcv-saas-area" id="meus-laudos">
      <div className="mcv-saas-summary">
        <div><span>Plano atual</span><strong>{panel?.plano_atual || 'Carregando'}</strong><small>{panel?.plan_id === 'free' ? 'PDF e histórico no PRO' : panel?.modo || 'Conta real'}</small></div>
        <div><span>Laudos no mês</span><strong>{panel ? `${panel.laudos_usados_mes}/${panel.limite_laudos}` : '--'}</strong><small>{panel?.laudos_restantes ?? '--'} restantes</small></div>
        <div><span>Veículos avaliados</span><strong>{panel?.total_veiculos ?? '--'}</strong><small>histórico do espaço</small></div>
        <div><span>Laudos salvos</span><strong>{panel?.total_laudos ?? '--'}</strong><small>com isolamento por conta</small></div>
      </div>
      <section className="mcv-dashboard-intelligence">
        <article><span>Inteligência da carteira</span><strong>{intelligence.premium}</strong><p>Leitura consolidada dos laudos salvos, liquidez declarada e confiança média das análises.</p></article>
        <div><small>Liquidez média</small><div className="mcv-score-progress dashboard"><span style={{ width: `${intelligence.liquidity}%` }} /></div><b>{intelligence.liquidity || '--'}%</b></div>
        <div><small>Confiança média</small><div className="mcv-score-progress dashboard"><span style={{ width: `${intelligence.confidence}%` }} /></div><b>{intelligence.confidence || '--'}%</b></div>
      </section>
      <div className="mcv-saas-grid">
        <article className="mcv-saas-table-card">
          <header><h2>Meus Laudos</h2><p>Histórico das análises geradas pela sua conta.</p></header>
          {!panel ? <PremiumSkeleton /> : reports.length ? (
            <div className="mcv-table-wrap"><table><thead><tr><th>Laudo</th><th>Valor</th><th>Liquidez</th><th>Confiança</th><th>Status</th></tr></thead><tbody>{reports.slice(0, 6).map((r) => <tr key={r.id}><td>{r.titulo}<small>{new Date(r.data).toLocaleDateString('pt-BR')}</small></td><td>{fmtCurrency(r.valor_recomendado || 0)}</td><td>{r.liquidez}</td><td>{r.confianca}</td><td>{r.status}</td></tr>)}</tbody></table></div>
          ) : <EmptyState text={panel?.features?.history === false ? "Histórico disponível no plano PRO." : "Nenhum laudo salvo ainda. Gere uma avaliação para iniciar o histórico."} />}
        </article>
        <article className="mcv-saas-table-card">
          <header><h2>Meus Veículos</h2><p>Veículos avaliados e disponíveis para nova análise.</p></header>
          {!panel ? <PremiumSkeleton /> : vehicles.length ? (
            <div className="mcv-table-wrap"><table><thead><tr><th>Veículo</th><th>Ano</th><th>Km</th><th>Região</th></tr></thead><tbody>{vehicles.slice(0, 6).map((v) => <tr key={v.id}><td>{v.veiculo}</td><td>{v.ano}</td><td>{v.km.toLocaleString('pt-BR')}</td><td>{v.cidade}/{v.estado}</td></tr>)}</tbody></table></div>
          ) : <EmptyState text="Nenhum veículo salvo ainda. As avaliações aparecerão aqui automaticamente." />}
        </article>
      </div>
    </section>
  );
}
