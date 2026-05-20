import type { ValuationResult } from '../../../types';

export async function exportReportPdf(result: ValuationResult) {
  const { exportValuationPdf } = await import('../../../lib/pdf');
  exportValuationPdf(result);
}
