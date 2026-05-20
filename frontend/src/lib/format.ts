export const fmtCurrency = (value: number) =>
  new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 }).format(value || 0);

export const pct = (value: number) => `${Math.round(value)}%`;
