import { Download, FileText, MessageSquareText } from 'lucide-react';
import { Button } from '../../../components/ui';
import { ConfidenceBadge } from '../../../design-system/report';

export function ReportHeader({ confidence, exporting, onExport, onAd }: { confidence: number; exporting: boolean; onExport: () => void; onAd: () => void }) {
  return (
    <header className="mcv-report-header">
      <div>
        <span><FileText size={15}/> Laudo Meu Carro Vale</span>
        <h2>Análise executiva do veículo</h2>
        <p>Documento profissional para leitura de mercado, faixa de valor e negociação.</p>
      </div>
      <div className="mcv-report-header-actions">
        <ConfidenceBadge value={confidence} />
        <Button variant="ghost" onClick={onAd}><MessageSquareText size={15}/> Gerar anúncio</Button>
        <Button variant="ghost" onClick={onExport} disabled={exporting}><Download size={15}/> {exporting ? 'Gerando...' : 'Exportar laudo'}</Button>
      </div>
    </header>
  );
}
