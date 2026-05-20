import { ExecutiveTable, ReportBlock } from '../../../design-system/report';
import { fmtCurrency } from '../../../lib/format';
import type { ValuationResult } from '../../../types';

export function ComparableTable({ result }: { result: ValuationResult }) {
  const v = result.valuation;
  const vehicleTitle = `${result.vehicle.brand} ${result.vehicle.model} ${result.vehicle.version}`;
  const explained = v.comparable_analysis || [];
  const comparables = v.comparables || [];
  const rows = explained.length
    ? explained.slice(0, 7).map((item) => [
      item.title || vehicleTitle,
      fmtCurrency(item.price),
      `${item.similarity_score}/100`,
      `${item.km_difference.toLocaleString('pt-BR')} km`,
      `${item.regional_similarity}/100`,
      `${item.valuation_impact >= 0 ? '+' : '-'} ${fmtCurrency(Math.abs(item.valuation_impact))}`,
      item.reading,
    ])
    : (comparables.length ? comparables.slice(0, 7) : [
      { title: vehicleTitle, price: v.market_reference, year: result.vehicle.year, mileage: result.vehicle.km, city: result.vehicle.city, state: result.vehicle.state, similarity_score: v.average_similarity_score || 91 },
    ]).map((item) => [
      item.title,
      fmtCurrency(item.price),
      `${item.similarity_score}/100`,
      `${item.mileage.toLocaleString('pt-BR')} km`,
      `${item.city}/${item.state}`,
      '-',
      'referência de mercado',
    ]);

  return (
    <ReportBlock eyebrow="Comparáveis explicados" title="Como cada referência influencia a análise">
      <ExecutiveTable columns={['Veículo', 'Preço', 'Similaridade', 'Dif. km', 'Região', 'Impacto', 'Leitura']} rows={rows} />
    </ReportBlock>
  );
}
