import type { VehicleInput } from '../types';

export const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8010';
const DEMO_MODE = import.meta.env.VITE_DEMO_MODE === 'true';

export type CatalogBrand = { id: number; vehicle_type: string; canonical_name: string; fipe_code: string; is_active: boolean };
export type CatalogModel = { id: number; brand_id: number; canonical_name: string; fipe_code: string; is_active: boolean };
export type CatalogVersion = { id: number; model_id: number; fipe_year_code: string; year: number; fuel: string; version_name: string; fipe_code: string; reference_month: string; fipe_price: number };

export async function loginUser(email: string, password: string) {
  const response = await fetch(`${API_URL}/api/auth/login`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email, password }) });
  if (!response.ok) throw new Error('E-mail ou senha inválidos');
  return response.json();
}

export async function registerUser(name: string, email: string, password: string, tenantName: string) {
  const response = await fetch(`${API_URL}/api/auth/register`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name, email, password, tenant_name: tenantName }) });
  if (!response.ok) { const data = await response.json().catch(() => ({})); throw new Error(data.detail || 'Não foi possível criar a conta'); }
  return response.json();
}

export async function loginDemo() {
  if (DEMO_MODE) {
    return {
      access_token: 'demo-token',
      refresh_token: 'demo-refresh-token',
      token_type: 'bearer',
    };
  }

  const response = await fetch(`${API_URL}/api/auth/demo`, {
    method: 'POST',
  });

  if (!response.ok) {
    throw new Error('Não foi possível abrir a demonstração');
  }

  return response.json();
}

export async function valuateVehicle(token: string, vehicle: VehicleInput) {
  const response = await fetch(`${API_URL}/api/vehicles/valuate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
    body: JSON.stringify(vehicle),
  });
  if (!response.ok) throw new Error('Não foi possível gerar o valuation');
  return response.json();
}

export async function fetchCatalogBrands(vehicleType = 'carros') {
  const response = await fetch(`${API_URL}/api/catalog/brands?vehicle_type=${encodeURIComponent(vehicleType)}`);
  if (!response.ok) return [] as CatalogBrand[];
  return response.json() as Promise<CatalogBrand[]>;
}

export async function fetchCatalogModels(brandId: number) {
  const response = await fetch(`${API_URL}/api/catalog/models?brand_id=${brandId}`);
  if (!response.ok) return [] as CatalogModel[];
  return response.json() as Promise<CatalogModel[]>;
}

export async function fetchCatalogVersions(modelId: number) {
  const response = await fetch(`${API_URL}/api/catalog/versions?model_id=${modelId}`);
  if (!response.ok) return [] as CatalogVersion[];
  return response.json() as Promise<CatalogVersion[]>;
}

export type CatalogSyncJob = {
  id: number;
  status: string;
  vehicle_type: string;
  total_brands: number;
  processed_brands: number;
  total_models: number;
  processed_models: number;
  total_versions: number;
  processed_versions: number;
  progress_percent: number;
  started_at?: string | null;
  finished_at?: string | null;
  error_message?: string;
  created_at?: string | null;
};

export type CatalogAdminOverview = {
  total_brands: number;
  total_models: number;
  total_versions: number;
  latest_sync: CatalogSyncJob | null;
  recent_errors: CatalogSyncJob[];
};

function authHeaders(token: string) {
  return { Authorization: `Bearer ${token}` };
}

export async function fetchCatalogAdminOverview(token: string) {
  const response = await fetch(`${API_URL}/api/catalog/admin/overview`, { headers: authHeaders(token) });
  if (!response.ok) throw new Error('Não foi possível carregar o painel do catálogo');
  return response.json() as Promise<CatalogAdminOverview>;
}

export async function startCatalogFipeSync(token: string, vehicleType = 'carros') {
  const response = await fetch(`${API_URL}/api/catalog/sync-fipe?vehicle_type=${encodeURIComponent(vehicleType)}`, { method: 'POST', headers: authHeaders(token) });
  if (!response.ok) throw new Error('Não foi possível iniciar a sincronização FIPE');
  return response.json() as Promise<{ message: string; job: CatalogSyncJob }>;
}

export async function fetchCatalogSyncStatus(token: string, jobId: number) {
  const response = await fetch(`${API_URL}/api/catalog/sync-status/${jobId}`, { headers: authHeaders(token) });
  if (!response.ok) throw new Error('Não foi possível consultar o progresso da sincronização');
  return response.json() as Promise<CatalogSyncJob>;
}

export type VehicleSuggestion = {
  brand: string;
  model: string;
  version: string;
  year: number | string;
  fuel: string;
  fipe_code?: string;
  confidence: number;
  display_name: string;
  source?: string;
};

export async function searchVehicles(query: string) {
  if (DEMO_MODE) {
    return [
      {
        brand: 'Chevrolet',
        model: 'Agile',
        version: 'LTZ 1.4 Flex',
        year: 2013,
        fuel: 'Flex',
        fipe_code: '004363-5',
        confidence: 96,
        display_name: 'Chevrolet Agile LTZ 1.4 Flex 2013',
        source: 'demo',
      },
      {
        brand: 'Toyota',
        model: 'Corolla',
        version: 'XEi 2.0 Flex',
        year: 2020,
        fuel: 'Flex',
        fipe_code: '002123-2',
        confidence: 95,
        display_name: 'Toyota Corolla XEi 2.0 Flex 2020',
        source: 'demo',
      },
    ].filter((item) =>
      item.display_name.toLowerCase().includes(query.toLowerCase())
    ) as VehicleSuggestion[];
  }

  const response = await fetch(
    `${API_URL}/api/search/vehicles?q=${encodeURIComponent(query)}`
  );

  if (!response.ok) {
    throw new Error('Motor de dados indisponível no momento.');
  }

  return response.json() as Promise<VehicleSuggestion[]>;
}

export async function autoValuateVehicle(token: string, payload: { query: string; mileage: number; state: string; city: string; condition: string; brand?: string; model?: string; version?: string; year?: number; transmission?: string; fuel?: string; color?: string; options?: string; history?: string; revisions?: string }) {
  const response = await fetch(`${API_URL}/api/vehicles/auto-valuate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data.detail || 'Não foi possível avaliar com o motor de dados.');
  }
  return response.json();
}
