import { fmtCurrency } from '../../lib/format';

export function MetricLine({ label, value, note, tone = 'default' }: { label: string; value: string; note?: string; tone?: 'default' | 'green' | 'gold' | 'danger' }) {
  return <div className={`mcv-metric-line mcv-tone-${tone}`}><span>{label}</span><strong>{value}</strong>{note ? <em>{note}</em> : null}</div>;
}

export function ValuationRange({ quick, ideal, recommendedTop }: { quick: number; ideal: number; recommendedTop: number }) {
  return (
    <section className="mcv-valuation-range">
      <div className="mcv-section-title"><p>Faixa de valor</p><h2>Valor recomendado para negociação</h2></div>
      <div className="mcv-range-track"><i style={{ left: '14%' }} /><b style={{ left: '52%' }} /><i style={{ left: '86%' }} /></div>
      <div className="mcv-range-values">
        <MetricLine label="Venda rápida" value={fmtCurrency(quick)} />
        <MetricLine label="Valor indicado" value={fmtCurrency(ideal)} tone="green" note="referência principal" />
        <MetricLine label="Faixa superior" value={fmtCurrency(recommendedTop)} tone="gold" />
      </div>
    </section>
  );
}

export function ConfidenceBadge({ value }: { value: number }) {
  return <span className="mcv-confidence"><b>{Math.round(value)}%</b> confiança</span>;
}

export function LiquidityBadge({ label, value }: { label: string; value: number }) {
  return <span className="mcv-liquidity"><b>{label}</b><i style={{ width: `${Math.max(8, Math.min(100, value))}%` }} /></span>;
}

export function VehicleSummary({ title, meta }: { title: string; meta: string[] }) {
  return <div className="mcv-vehicle-summary"><p>Veículo analisado</p><h3>{title}</h3><div>{meta.map((item) => <span key={item}>{item}</span>)}</div></div>;
}

export function ExecutiveTable({ columns, rows }: { columns: string[]; rows: Array<Array<React.ReactNode>> }) {
  return <div className="mcv-table-wrap"><table className="mcv-exec-table"><thead><tr>{columns.map((c) => <th key={c}>{c}</th>)}</tr></thead><tbody>{rows.map((row, i) => <tr key={i}>{row.map((cell, j) => <td key={j}>{cell}</td>)}</tr>)}</tbody></table></div>;
}

export function MethodologyBox({ items }: { items: { label: string; value: string }[] }) {
  return <div className="mcv-methodology-box">{items.map((item) => <div key={item.label}><span>{item.label}</span><strong>{item.value}</strong></div>)}</div>;
}

export function ReportBlock({ eyebrow, title, children }: { eyebrow: string; title: string; children: React.ReactNode }) {
  return <section className="mcv-report-block"><div className="mcv-section-title"><p>{eyebrow}</p><h2>{title}</h2></div>{children}</section>;
}

export function MarketTemperatureBar({ label, value }: { label: string; value: number }) {
  const safe = Math.max(0, Math.min(100, Math.round(value || 0)));
  return (
    <div className="mcv-market-temperature-bar" aria-label={`Temperatura de mercado: ${label}`}>
      <div className="mcv-temp-head"><span>{label}</span><b>{safe}/100</b></div>
      <div className="mcv-temp-track"><i style={{ width: `${Math.max(6, safe)}%` }} /></div>
      <div className="mcv-temp-scale"><span>Baixa demanda</span><span>Estável</span><span>Muito aquecido</span></div>
    </div>
  );
}
