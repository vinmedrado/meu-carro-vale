import { Suspense, lazy } from 'react';
import { AlertTriangle } from 'lucide-react';
import { Shell } from '../components/layout/Shell';
import { LoadingExperience } from '../components/motion/LoadingExperience';
import { VehicleOnboarding } from '../features/vehicle/VehicleOnboarding';
import { AuthPage } from '../features/auth/AuthPage';
import { SaasDashboard } from '../features/saas/SaasDashboard';
import { useValuationFlow } from '../hooks/useValuationFlow';

const LandingPage = lazy(() => import('../features/landing/LandingPage').then((m) => ({ default: m.LandingPage })));
const ValuationReport = lazy(() => import('../features/report/ValuationReport').then((m) => ({ default: m.ValuationReport })));
const CatalogAdminPanel = lazy(() => import('../features/catalog/CatalogAdminPanel').then((m) => ({ default: m.CatalogAdminPanel })));
const MarketDataQualityPanel = lazy(() => import('../features/market/MarketDataQualityPanel').then((m) => ({ default: m.MarketDataQualityPanel })));
const AdminDataOperationsCenter = lazy(() => import('../features/admin/AdminDataOperationsCenter').then((m) => ({ default: m.AdminDataOperationsCenter })));

function AdminRouteUnavailable() {
  return (
    <main className="mcv-landing-final">
      <section className="mcv-landing-hero">
        <div className="mcv-hero-copy">
          <p>Acesso interno</p>
          <h1>Painel administrativo indisponível.</h1>
          <span>Este ambiente não está configurado para exibir ferramentas internas.</span>
          <div className="mcv-hero-actions"><a href="/">Voltar para avaliação</a></div>
        </div>
      </section>
    </main>
  );
}

export default function App() {
  const { token, vehicle, setVehicle, result, loading, error, login, register, enterDemo, generateValuation, logout } = useValuationFlow();
  const showAdminTools = import.meta.env.VITE_SHOW_ADMIN_TOOLS === 'true';
  const demoMode = import.meta.env.VITE_DEMO_MODE === 'true';
  const isAdminRoute = window.location.pathname === '/admin/data-operations';
  const adminRouteToken = token || localStorage.getItem('token') || localStorage.getItem('access_token') || (demoMode ? 'demo-token' : '');

  if (isAdminRoute) {
    if (!showAdminTools) {
      return <AdminRouteUnavailable />;
    }

    return (
      <Shell onLogout={logout} showAdminTools={showAdminTools}>
        {error && <div className="mcv-error"><AlertTriangle size={16} /> {error}</div>}
        <Suspense fallback={<LoadingExperience title="Carregando operações de dados..." />}>
          <AdminDataOperationsCenter token={adminRouteToken} />
        </Suspense>
      </Shell>
    );
  }

  if (!token) {
    return (
      <Suspense fallback={<LoadingExperience fullScreen title="Preparando Meu Carro Vale..." />}>
        {demoMode ? <LandingPage onDemo={enterDemo} loading={loading} error={error} /> : <><LandingPage onDemo={enterDemo} loading={loading} error={error} /><AuthPage onLogin={login} onRegister={register} onDemo={enterDemo} loading={loading} error={error} /></>}
      </Suspense>
    );
  }

  return (
    <Shell onLogout={logout} showAdminTools={showAdminTools}>
      {error && <div className="mcv-error"><AlertTriangle size={16} /> {error}</div>}
      <Suspense fallback={<LoadingExperience title="Carregando análise..." />}>
        <section className="mcv-product-flow">
          <VehicleOnboarding vehicle={vehicle} setVehicle={setVehicle} onValuate={generateValuation} loading={loading} hasResult={Boolean(result)} />
          {result ? <ValuationReport result={result} /> : null}
        </section>
        <SaasDashboard token={token} />
        {showAdminTools ? (
          <section id="meus-veiculos" className="mcv-admin-compact">
            <details>
              <summary>Catálogo FIPE</summary>
              <CatalogAdminPanel token={token} />
            </details>
            <details>
              <summary>Qualidade dos Dados de Mercado</summary>
              <MarketDataQualityPanel token={token} />
            </details>
            <details>
              <summary>Operações de Dados</summary>
              <AdminDataOperationsCenter token={token} />
            </details>
          </section>
        ) : null}
      </Suspense>
    </Shell>
  );
}
