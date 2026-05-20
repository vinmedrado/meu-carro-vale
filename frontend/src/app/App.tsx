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

export default function App() {
  const { token, vehicle, setVehicle, result, loading, error, login, register, enterDemo, generateValuation, logout } = useValuationFlow();

  if (!token) {
    return (
      <Suspense fallback={<LoadingExperience fullScreen title="Preparando Meu Carro Vale..." />}>
        <><LandingPage onDemo={enterDemo} loading={loading} error={error} /><AuthPage onLogin={login} onRegister={register} onDemo={enterDemo} loading={loading} error={error} /></>
      </Suspense>
    );
  }

  return (
    <Shell onLogout={logout}>
      {error && <div className="mcv-error"><AlertTriangle size={16} /> {error}</div>}
      <Suspense fallback={<LoadingExperience title="Carregando análise..." />}>
        <section className="mcv-product-flow">
          <VehicleOnboarding vehicle={vehicle} setVehicle={setVehicle} onValuate={generateValuation} loading={loading} hasResult={Boolean(result)} />
          {result ? <ValuationReport result={result} /> : null}
        </section>
        <SaasDashboard token={token} />
        <section id="meus-veiculos" className="mcv-admin-compact">
          <details>
            <summary>Catálogo FIPE</summary>
            <CatalogAdminPanel token={token} />
          </details>
        </section>
      </Suspense>
    </Shell>
  );
}
