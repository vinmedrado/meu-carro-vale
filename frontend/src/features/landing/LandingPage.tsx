import { AlertTriangle, ArrowRight, BadgeCheck, BarChart3, CarFront, FileText, Loader2, Scale, ShieldCheck } from 'lucide-react';
import { Button } from '../../components/ui';
import { Logo } from '../../components/branding/Logo';

export function LandingPage({ onDemo, loading = false, error = '' }: { onDemo: () => void; loading?: boolean; error?: string }) {
  return (
    <main className="mcv-landing-final">
      <header className="mcv-landing-header"><Logo /><button onClick={onDemo} disabled={loading}>Avaliar meu veículo</button></header>
      <section className="mcv-landing-hero">
        <div className="mcv-hero-copy">
          <p>Seu veículo como um patrimônio</p>
          <h1>Descubra quanto seu carro realmente vale.</h1>
          <span>Use dados de mercado, FIPE e comparáveis para negociar com mais segurança.</span>
          {error ? <div className="mcv-error"><AlertTriangle size={16}/>{error}</div> : null}
          <div className="mcv-hero-actions"><Button onClick={onDemo} disabled={loading}>{loading ? <Loader2 className="animate-spin" size={16}/> : null} Avaliar meu veículo <ArrowRight size={16}/></Button><a href="#como-funciona">Entender antes de vender</a></div>
        </div>
        <LaudoMockup />
      </section>

      <section id="como-funciona" className="mcv-editorial-section">
        <div className="mcv-section-title"><p>Antes de vender, entenda o mercado</p><h2>Uma análise para negociar, não apenas consultar preço.</h2></div>
        <div className="mcv-steps-grid">
          <Step n="01" title="Informe o veículo" text="Marca, modelo, versão, ano, quilometragem e praça de venda." />
          <Step n="02" title="Compare com o mercado" text="A plataforma cruza FIPE, anúncios semelhantes e liquidez regional." />
          <Step n="03" title="Receba o laudo" text="Uma faixa de valor clara, com metodologia e argumentos de negociação." />
        </div>
      </section>

      <section className="mcv-editorial-section">
        <div className="mcv-section-title"><p>Ambientes do produto</p><h2>Valor, mercado e laudo em uma jornada simples.</h2></div>
        <div className="mcv-product-rooms">
          <Room icon={<Scale size={16}/>} title="Valor" text="Faixa recomendada para anúncio, venda rápida e negociação." />
          <Room icon={<BarChart3 size={16}/>} title="Mercado" text="Liquidez, oferta, procura e comportamento regional." />
          <Room icon={<BadgeCheck size={16}/>} title="Comparáveis" text="Anúncios semelhantes organizados em tabela executiva." />
          <Room icon={<FileText size={16}/>} title="Laudo" text="Documento profissional para apoiar a tomada de decisão." />
          <Room icon={<ShieldCheck size={16}/>} title="Negociação" text="Pontos objetivos para defender o valor do veículo." />
        </div>
      </section>

      <section className="mcv-proof-section">
        <PanelMockup />
        <div>
          <div className="mcv-section-title"><p>Produto brasileiro</p><h2>Feito para a realidade de venda nacional.</h2></div>
          <p>O Meu Carro Vale organiza dados de referência, praça, quilometragem e comparáveis em uma leitura clara para proprietários, lojas e consultores automotivos.</p>
          <Button onClick={onDemo} disabled={loading}>Avaliar meu veículo</Button>
        </div>
      </section>
    </main>
  );
}

function LaudoMockup() {
  return <aside className="mcv-laudo-mock"><div><span>Laudo Meu Carro Vale</span><CarFront size={16}/></div><h2>R$ 89.400</h2><p>Valor indicado para negociação</p><i/><section><b>Venda rápida</b><strong>R$ 82.900</strong></section><section><b>Valor competitivo</b><strong>R$ 96.100</strong></section><footer>Boa liquidez regional • 12 comparáveis • confiança 88%</footer></aside>;
}
function PanelMockup(){return <div className="mcv-panel-mock"><span>Painel executivo</span><h3>Faixa de Valor</h3><div className="mcv-mock-line"><i/><i/><i/></div><div className="mcv-mock-table"><p><b>FIPE</b><strong>R$ 80.300</strong></p><p><b>Mercado</b><strong>R$ 89.400</strong></p><p><b>Liquidez</b><strong>Alta</strong></p></div></div>}
function Step({ n, title, text }: { n: string; title: string; text: string }) { return <article className="mcv-step"><span>{n}</span><h3>{title}</h3><p>{text}</p></article>; }
function Room({ icon, title, text }: { icon: React.ReactNode; title: string; text: string }) { return <article className="mcv-room"><span>{icon}</span><h3>{title}</h3><p>{text}</p></article>; }
