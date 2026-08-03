import type { ValuationResult } from "../types";
import { exportReportPdf } from "../features/report/report/PdfExport";

export async function exportValuationPdf(result: ValuationResult) {
  await exportReportPdf(result);
}
