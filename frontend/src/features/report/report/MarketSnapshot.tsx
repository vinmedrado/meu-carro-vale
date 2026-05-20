import { ExecutiveTable, ReportBlock } from '../../../design-system/report';
import { fmtCurrency } from '../../../lib/format';
import type { ValuationResult } from '../../../types';

export function MarketSnapshot({ result }: { result: ValuationResult }) {
  const v = result.valuation;
  return (
    <ReportBlock eyebrow="Retrato de mercado" title="Leitura compacta da praça">
      <ExecutiveTable
        columns={['Referência', 'Valor', 'Interpretação']}
        rows={[
          ['FIPE', fmtCurrency(v.fipe_real || v.fipe_simulated), 'Piso técnico usado na comparação'],
          ['Valor de mercado', fmtCurrency(v.market_reference), 'Leitura da amostra disponível'],
          ['Valor indicado', fmtCurrency(v.ideal_price), 'Referência central do laudo'],
          ['Piso de negociação', fmtCurrency(v.negotiation_floor || v.negotiation_range?.[0] || v.quick_sale_price), 'Limite defensável para proposta'],
          ['Teto de negociação', fmtCurrency(v.negotiation_ceiling || v.negotiation_range?.[1] || v.market_reference), 'Valor máximo para ancoragem'],
        ]}
      />
    </ReportBlock>
  );
}
