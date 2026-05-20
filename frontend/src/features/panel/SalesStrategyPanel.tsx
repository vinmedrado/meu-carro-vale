import { useMemo, useState } from 'react';
import type { ValuationResult } from '../../types';
import { fmtCurrency } from '../../lib/format';

type Props = { result: ValuationResult | null };

function normalizeMoney(value: string) {
  const digits = value.replace(/\D/g, '');
  return digits ? Number(digits) : 0;
}

function classifyProposal(value: number, min: number, low: number) {
  if (!value) return { tone: 'neutral', title: 'Simule uma proposta', text: 'Digite o valor que recebeu para comparar com a faixa recomendada.' };
  if (value >= min) return { tone: 'green', title: 'Boa proposta', text: 'A proposta está dentro ou acima da faixa ideal de fechamento.' };
  if (value >= low) return { tone: 'yellow', title: 'Negociar com cuidado', text: 'Ainda pode fazer sentido, mas tente aproximar da faixa ideal antes de aceitar.' };
  return { tone: 'red', title: 'Proposta abaixo do recomendado', text: 'Você pode estar deixando dinheiro na mesa. Use os argumentos do laudo para defender o valor.' };
}

export function SalesStrategyPanel({ result }: Props) {
  const v = result?.valuation;
  const decision = v?.selling_decision || {};
  const listing = v?.listing_price || decision.listing_price || v?.recommended_listing_price || v?.ideal_price || 0;
  const closeMin = v?.ideal_close_range_min || decision.ideal_close_range_min || v?.safe_price_range?.[0] || v?.negotiation_floor || v?.quick_sale_price || 0;
  const closeMax = v?.ideal_close_range_max || decision.ideal_close_range_max || v?.safe_price_range?.[1] || v?.negotiation_ceiling || v?.ideal_price || 0;
  const minimum = v?.minimum_recommended_price || decision.minimum_recommended_price || v?.quick_sale_price || closeMin;
  const resistance = v?.resistance_price || decision.resistance_price || v?.probable_ceiling || v?.negotiation_ceiling || closeMax;
  const [proposal, setProposal] = useState('');
  const proposalValue = normalizeMoney(proposal);
  const signal = useMemo(() => classifyProposal(proposalValue, closeMin, minimum), [proposalValue, closeMin, minimum]);

  if (!result) {
    return (
      <section className="mcv-sales-strategy-panel mcv-sales-empty">
        <div className="mcv-section-title"><p>Estratégia de Venda</p><h2>Preencha o veículo para receber orientação comercial.</h2></div>
        <p>O painel vai indicar preço para anunciar, faixa ideal para fechar, risco de ficar parado e defesa do valor.</p>
      </section>
    );
  }

  const defense = v?.price_defense_arguments || decision.price_defense_arguments || [];

  return (
    <section className="mcv-sales-strategy-panel">
      <div className="mcv-sales-head">
        <div className="mcv-section-title"><p>Estratégia de Venda</p><h2>Por quanto anunciar e como negociar</h2></div>
        <span className={`mcv-stuck-risk mcv-risk-${String(v?.stuck_risk_level || decision.stuck_risk_level || 'Moderado').toLowerCase()}`}>Risco de ficar parado: {v?.stuck_risk_level || decision.stuck_risk_level || 'Moderado'}</span>
      </div>

      <div className="mcv-sales-strip">
        <div><span>Preço para anunciar</span><strong>{fmtCurrency(listing)}</strong><em>{v?.psychological_price_note || decision.psychological_price_note || 'Preço com leitura comercial para anúncio.'}</em></div>
        <div><span>Faixa ideal para fechar</span><strong>{fmtCurrency(closeMin)} a {fmtCurrency(closeMax)}</strong><em>Use essa faixa como referência de negociação.</em></div>
        <div><span>Evite aceitar abaixo de</span><strong>{fmtCurrency(minimum)}</strong><em>Valor mínimo recomendado pela análise.</em></div>
        <div><span>Acima de</span><strong>{fmtCurrency(resistance)}</strong><em>Maior resistência esperada do mercado.</em></div>
      </div>

      <div className="mcv-sales-grid">
        <div className="mcv-proposal-box">
          <div className="mcv-section-title"><p>Semáforo da Negociação</p><h2>Simular proposta recebida</h2></div>
          <label>Valor da proposta</label>
          <input value={proposal} onChange={(event) => setProposal(event.target.value)} placeholder="Ex.: R$ 110.000" inputMode="numeric" />
          <div className={`mcv-proposal-result mcv-signal-${signal.tone}`}><strong>{signal.title}</strong><p>{signal.text}</p></div>
        </div>
        <div className="mcv-defense-box">
          <div className="mcv-section-title"><p>Defesa do preço</p><h2>Como defender esse valor</h2></div>
          <ul>{defense.slice(0, 5).map((item) => <li key={item}>{item}</li>)}</ul>
        </div>
      </div>

      <div className="mcv-review-box">
        <strong>Quando revisar o preço</strong>
        <p>Se não receber contatos em {v?.review_price_after_days || decision.review_price_after_days || 10} dias, reduza entre {v?.suggested_price_cut_percent || decision.suggested_price_cut_percent || 2}% e 3%. Se receber muitas propostas abaixo da faixa, revise fotos e descrição antes de baixar.</p>
        <p>{v?.seller_summary || decision.seller_summary}</p>
      </div>
    </section>
  );
}
