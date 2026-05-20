import { ReportBlock, ExecutiveTable } from '../../../design-system/report';
import { fmtCurrency } from '../../../lib/format';
import type { ValuationResult } from '../../../types';

export function ExplainableValuation({ result }: { result: ValuationResult }) {
  const v = result.valuation;
  const factors = Array.isArray(v.valuation_explanation) ? v.valuation_explanation : [];
  return (
    <ReportBlock eyebrow="Valuation explicado" title="Por que chegamos nessa faixa">
      <p className="mcv-muted-text">
        {v.valuation_explanation_text || 'A faixa combina comparáveis, região, quilometragem, liquidez, dispersão de preços e qualidade da amostra.'}
      </p>
      {factors.length ? (
        <ExecutiveTable
          columns={['Fator', 'Impacto', 'Peso', 'Leitura']}
          rows={factors.map((item) => [
            item.factor,
            `${item.impact_value >= 0 ? '+' : '-'} ${fmtCurrency(Math.abs(item.impact_value))}`,
            `${item.weight}%`,
            item.reason,
          ])}
        />
      ) : null}
    </ReportBlock>
  );
}
