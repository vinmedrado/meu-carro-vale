import { MethodologyBox, ReportBlock } from '../../../design-system/report';
import type { ValuationResult } from '../../../types';

export function MethodologySection({ result }: { result: ValuationResult }) {
  const v = result.valuation;
  const comparables = v.comparables || [];
  const methodology = v.mcv_intelligence?.methodology as string[] | undefined;
  return (
    <ReportBlock eyebrow="Metodologia" title="Como a faixa de valor foi calculada">
      <p className="mcv-muted-text">{v.valuation_explanation_text || v.methodology_summary || 'A análise combina referência FIPE, comportamento do mercado real, região, quilometragem, ano, conservação e comparáveis semelhantes para gerar uma faixa defensável de negociação.'}</p>
      {methodology?.length ? <ul className="mcv-methodology-list">{methodology.map((item) => <li key={item}>{item}</li>)}</ul> : null}
      <MethodologyBox items={[
        { label: 'Fonte FIPE', value: v.fipe_source || 'Referência configurada' },
        { label: 'Comparáveis usados', value: String(v.comparables_used ?? v.comparable_count ?? comparables.length) },
        { label: 'Outliers removidos', value: String(v.outliers_removed ?? 0) },
        { label: 'Similaridade média', value: `${v.similarity_score ?? v.average_similarity_score ?? '-'}/100` },
        { label: 'Aderência regional', value: `${v.regional_similarity ?? '-'} / 100` },
        { label: 'Qualidade', value: v.analysis_quality || v.confidence_level || 'em análise' },
      ]} />
    </ReportBlock>
  );
}
