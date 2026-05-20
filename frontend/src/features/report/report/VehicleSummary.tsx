import { VehicleSummary as VehicleSummaryCard } from '../../../design-system/report';
import type { ValuationResult } from '../../../types';

export function VehicleSummary({ result, generatedAt }: { result: ValuationResult; generatedAt: string }) {
  const title = `${result.vehicle.brand} ${result.vehicle.model} ${result.vehicle.version}`;
  return <VehicleSummaryCard title={title} meta={[String(result.vehicle.year), `${result.vehicle.km.toLocaleString('pt-BR')} km`, `${result.vehicle.city}/${result.vehicle.state}`, `Gerado em ${generatedAt}`]} />;
}
