import { RefreshCw, AlertTriangle, Database, CheckCircle2 } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { Button, Surface } from '../../components/ui';
import { fetchCatalogAdminOverview, fetchCatalogSyncStatus, startCatalogFipeSync, type CatalogAdminOverview, type CatalogSyncJob } from '../../lib/api';

export function CatalogAdminPanel({ token }: { token: string }) {
  const [overview, setOverview] = useState<CatalogAdminOverview | null>(null);
  const [activeJob, setActiveJob] = useState<CatalogSyncJob | null>(null);
  const [vehicleType, setVehicleType] = useState('carros');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function load() {
    try {
      const data = await fetchCatalogAdminOverview(token);
      setOverview(data);
      if (data.latest_sync && ['pending', 'running'].includes(data.latest_sync.status)) setActiveJob(data.latest_sync);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar catálogo');
    }
  }

  useEffect(() => { load(); }, [token]);

  useEffect(() => {
    if (!activeJob || !['pending', 'running'].includes(activeJob.status)) return;
    const timer = window.setInterval(async () => {
      try {
        const job = await fetchCatalogSyncStatus(token, activeJob.id);
        setActiveJob(job);
        if (!['pending', 'running'].includes(job.status)) load();
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Falha ao atualizar progresso');
      }
    }, 2500);
    return () => window.clearInterval(timer);
  }, [activeJob?.id, activeJob?.status, token]);

  const latest = activeJob || overview?.latest_sync || null;
  const progress = useMemo(() => Math.max(0, Math.min(100, latest?.progress_percent || 0)), [latest]);

  async function startSync() {
    setLoading(true); setError('');
    try {
      const response = await startCatalogFipeSync(token, vehicleType);
      setActiveJob(response.job);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao iniciar sincronização');
    } finally {
      setLoading(false);
    }
  }

  return (
    <Surface id="catalogo" className="p-4 md:p-5">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="eyebrow">Catálogo mestre</p>
          <h2 className="mt-2 text-xl font-semibold tracking-[-0.03em]">Base FIPE normalizada</h2>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-ash">Controle interno de marcas, modelos, versões, aliases brasileiros e sincronização FIPE em background.</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <select className="admin-select" value={vehicleType} onChange={(e) => setVehicleType(e.target.value)}>
            <option value="carros">Carros</option>
            <option value="motos">Motos</option>
            <option value="caminhoes">Caminhões</option>
          </select>
          <Button onClick={startSync} disabled={loading || latest?.status === 'running'}>
            <RefreshCw size={17} className={loading ? 'animate-spin' : ''} /> Sincronizar FIPE
          </Button>
        </div>
      </div>

      {error && <div className="mt-4 flex items-center gap-2 rounded-[18px] border border-red-400/20 bg-red-400/10 p-3 text-sm text-red-100"><AlertTriangle size={16}/>{error}</div>}

      <div className="mt-6 grid gap-3 md:grid-cols-3">
        <Metric icon={<Database size={18}/>} label="Marcas" value={overview?.total_brands || 0} />
        <Metric icon={<Database size={18}/>} label="Modelos" value={overview?.total_models || 0} />
        <Metric icon={<Database size={18}/>} label="Versões" value={overview?.total_versions || 0} />
      </div>

      <div className="mt-5 rounded-[24px] mcv-muted-panel p-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-sm font-semibold mcv-text">Última sincronização</p>
            <p className="mt-1 text-xs text-ash">Status: {latest?.status || 'sem execução'} • Tipo: {latest?.vehicle_type || '-'}</p>
          </div>
          <div className="flex items-center gap-2 text-xs text-gold"><CheckCircle2 size={15}/>{progress}%</div>
        </div>
        <div className="mt-3 h-2 overflow-hidden rounded-full mcv-bar-bg">
          <div className="h-full rounded-full bg-gradient-to-r from-[var(--mcv-gold)] to-[var(--mcv-green)] transition-all" style={{ width: `${progress}%` }} />
        </div>
        <div className="mt-3 grid gap-2 text-xs text-ash sm:grid-cols-3">
          <span>Marcas: {latest?.processed_brands || 0}/{latest?.total_brands || 0}</span>
          <span>Modelos: {latest?.processed_models || 0}/{latest?.total_models || 0}</span>
          <span>Versões: {latest?.processed_versions || 0}/{latest?.total_versions || 0}</span>
        </div>
        {latest?.error_message && <p className="mt-3 text-xs text-red-100">Erro recente: {latest.error_message}</p>}
      </div>
    </Surface>
  );
}

function Metric({ icon, label, value }: { icon: React.ReactNode; label: string; value: number }) {
  return <div className="rounded-[22px] mcv-muted-panel p-4"><div className="text-gold">{icon}</div><p className="mt-3 text-xs uppercase tracking-[0.18em] text-ash">{label}</p><strong className="mt-1 block text-2xl tracking-[-0.04em] mcv-text">{value.toLocaleString('pt-BR')}</strong></div>;
}
