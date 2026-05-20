import { Check, Loader2, Search, SlidersHorizontal } from 'lucide-react';
import { useEffect, useState } from 'react';
import type { VehicleInput } from '../../types';
import { fetchCatalogBrands, fetchCatalogModels, fetchCatalogVersions, type CatalogBrand, type CatalogModel, type CatalogVersion, type VehicleSuggestion } from '../../lib/api';
import { Button, Surface } from '../../components/ui';
import { VehicleSearchBox } from './VehicleSearchBox';

export function VehicleOnboarding({ vehicle, setVehicle, onValuate, loading, hasResult = false }: { vehicle: VehicleInput; setVehicle: (v: VehicleInput) => void; onValuate: () => void; loading: boolean; hasResult?: boolean }) {
  const [step, setStep] = useState(0);
  const [toast, setToast] = useState('');
  const [vehicleType, setVehicleType] = useState(vehicle.vehicle_type || 'carros');
  const [brands, setBrands] = useState<CatalogBrand[]>([]);
  const [models, setModels] = useState<CatalogModel[]>([]);
  const [versions, setVersions] = useState<CatalogVersion[]>([]);
  const [selectedBrandId, setSelectedBrandId] = useState<number | ''>('');
  const [selectedModelId, setSelectedModelId] = useState<number | ''>('');
  const hasVehicle = Boolean(vehicle.brand || vehicle.model || vehicle.query);
  const canGenerate = hasVehicle && vehicle.km > 0 && Boolean(vehicle.city && vehicle.state && vehicle.condition);

  function patch(key: keyof VehicleInput, value: string | number | string[]) {
    setVehicle({ ...vehicle, [key]: value });
  }

  useEffect(() => { fetchCatalogBrands(vehicleType).then(setBrands).catch(() => setBrands([])); }, [vehicleType]);
  useEffect(() => { if (!selectedBrandId) { setModels([]); return; } fetchCatalogModels(Number(selectedBrandId)).then(setModels).catch(() => setModels([])); }, [selectedBrandId]);
  useEffect(() => { if (!selectedModelId) { setVersions([]); return; } fetchCatalogVersions(Number(selectedModelId)).then(setVersions).catch(() => setVersions([])); }, [selectedModelId]);

  function showToast(message: string) {
    setToast(message);
    window.setTimeout(() => setToast(''), 2000);
  }

  function applyVehicleSuggestion(suggestion: VehicleSuggestion, query: string) {
    setVehicle({
      ...vehicle,
      query,
      brand: suggestion.brand || vehicle.brand,
      model: suggestion.model || vehicle.model,
      version: suggestion.version || vehicle.version,
      year: Number(suggestion.year || vehicle.year),
      fuel: suggestion.fuel || vehicle.fuel,
      fipe_code: suggestion.fipe_code || vehicle.fipe_code,
    });
    setStep(1);
    showToast('Veículo selecionado.');
  }

  function generate() {
    if (!canGenerate) {
      setStep(hasVehicle ? 1 : 0);
      showToast('Complete os campos principais.');
      return;
    }
    setStep(2);
    onValuate();
  }

  return (
    <Surface id="avaliacao" className="mcv-guided-card">
      <div className="mcv-hero-clean">
        <p className="mcv-kicker">Avaliação rápida</p>
        <h1>Quanto seu carro vale hoje?</h1>
        <span>Busque o veículo, informe quilometragem e região para receber uma estratégia de venda.</span>
      </div>

      <div className="mcv-stepper-clean" aria-label="Etapas da avaliação">
        {['Buscar veículo', 'Completar dados', 'Resultado da análise'].map((label, index) => (
          <button key={label} onClick={() => setStep(index)} className={index === step ? 'active' : ''}>
            <strong>{index + 1}</strong><span>{label}</span>
          </button>
        ))}
      </div>

      <div className="mcv-step-content-clean">
        {step === 0 ? (
          <section className="mcv-step-card-clean">
            <div className="mcv-step-title"><Search size={19} /><div><h2>Buscar veículo</h2><p>Digite modelo, versão ou ano.</p></div></div>
            <VehicleSearchBox onSelect={applyVehicleSuggestion} />
            <details className="mcv-manual-details">
              <summary>Não encontrei. Preencher manualmente</summary>
              <Grid>
                <Select label="Tipo" value={vehicleType} onChange={(v) => { setVehicleType(v); patch('vehicle_type', v); setSelectedBrandId(''); setSelectedModelId(''); }}>
                  <option value="carros">Carros</option><option value="motos">Motos</option><option value="caminhoes">Caminhões</option>
                </Select>
                {brands.length ? <Select label="Marca" value={selectedBrandId} onChange={(v) => { const id = Number(v); setSelectedBrandId(id); setSelectedModelId(''); const brand = brands.find((item) => item.id === id); if (brand) patch('brand', brand.canonical_name); }}><option value="">Selecione</option>{brands.map((brand) => <option key={brand.id} value={brand.id}>{brand.canonical_name}</option>)}</Select> : <Field label="Marca" value={vehicle.brand} onChange={(v) => patch('brand', v)} />}
                {models.length ? <Select label="Modelo" value={selectedModelId} onChange={(v) => { const id = Number(v); setSelectedModelId(id); const model = models.find((item) => item.id === id); if (model) patch('model', model.canonical_name); }}><option value="">Selecione</option>{models.map((model) => <option key={model.id} value={model.id}>{model.canonical_name}</option>)}</Select> : <Field label="Modelo" value={vehicle.model} onChange={(v) => patch('model', v)} />}
                {versions.length ? <Select label="Versão/Ano" value="" onChange={(v) => { const version = versions.find((item) => String(item.id) === v); if (version) { patch('version', version.version_name); patch('year', version.year); patch('fuel', version.fuel); } }}><option value="">Selecione</option>{versions.map((version) => <option key={version.id} value={version.id}>{version.version_name} • {version.year}</option>)}</Select> : <Field label="Versão" value={vehicle.version} onChange={(v) => patch('version', v)} />}
                <Field label="Ano" value={vehicle.year} type="number" onChange={(v) => patch('year', Number(v))} />
              </Grid>
            </details>
            <div className="mcv-step-actions-clean"><Button onClick={() => setStep(1)}>Continuar</Button></div>
          </section>
        ) : null}

        {step === 1 ? (
          <section className="mcv-step-card-clean">
            <div className="mcv-step-title"><SlidersHorizontal size={19} /><div><h2>Completar dados</h2><p>Só o essencial para calcular.</p></div></div>
            <Grid>
              <Field label="Quilometragem" value={vehicle.km} type="number" onChange={(v) => patch('km', Number(v))} />
              <Field label="Estado" value={vehicle.state} onChange={(v) => patch('state', v.toUpperCase())} />
              <Field label="Cidade" value={vehicle.city} onChange={(v) => patch('city', v)} />
              <Select label="Condição" value={vehicle.condition} onChange={(v) => patch('condition', v)}>
                <option value="">Selecione</option><option value="Excelente">Excelente</option><option value="Boa">Boa</option><option value="Regular">Regular</option>
              </Select>
            </Grid>
            <details className="mcv-manual-details">
              <summary>Detalhes opcionais</summary>
              <Grid>
                <Field label="Câmbio" value={vehicle.transmission} onChange={(v) => patch('transmission', v)} />
                <Field label="Combustível" value={vehicle.fuel} onChange={(v) => patch('fuel', v)} />
                <Field label="Cor" value={vehicle.color} onChange={(v) => patch('color', v)} />
                <Field label="Opcionais" value={vehicle.options} onChange={(v) => patch('options', v)} />
              </Grid>
            </details>
            <div className="mcv-step-actions-clean"><Button variant="ghost" onClick={() => setStep(0)}>Voltar</Button><Button onClick={generate} disabled={loading}>{loading ? <Loader2 className="animate-spin" size={18} /> : null} Gerar análise</Button></div>
          </section>
        ) : null}

        {step === 2 ? (
          <section className="mcv-step-card-clean mcv-result-ready-card">
            <div className="mcv-step-title"><Check size={19} /><div><h2>Resultado da análise</h2><p>{hasResult ? 'Veja o preço e a estratégia.' : 'Gere a análise para ver o resultado.'}</p></div></div>
            <Button onClick={generate} disabled={loading}>{loading ? <Loader2 className="animate-spin" size={18} /> : null} Gerar novamente</Button>
          </section>
        ) : null}
      </div>
      <Toast message={toast} />
    </Surface>
  );
}

function Grid({ children }: { children: React.ReactNode }) { return <div className="mcv-form-grid-clean">{children}</div>; }

function Field({ label, value, onChange, type = 'text' }: { label: string; value: string | number; onChange: (v: string) => void; type?: string }) {
  return <label className="mcv-field-clean"><span>{label}</span><input value={value} type={type} onChange={(e) => onChange(e.target.value)} /></label>;
}

function Select({ label, value, onChange, children }: { label: string; value: string | number; onChange: (v: string) => void; children: React.ReactNode }) {
  return <label className="mcv-field-clean"><span>{label}</span><select value={value} onChange={(e) => onChange(e.target.value)}>{children}</select></label>;
}

function Toast({ message }: { message: string }) {
  if (!message) return null;
  return <div className="mcv-toast mcv-soft-enter"><Check size={17} />{message}</div>;
}
