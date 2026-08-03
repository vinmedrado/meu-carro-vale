import { AlertTriangle, ArrowRight, BarChart3, BadgeCheck, CarFront, FileText, Loader2, Search, ShieldCheck, Sparkles } from 'lucide-react';
import { motion } from 'framer-motion';
import { Button } from '../../components/ui';
import { Logo } from '../../components/branding/Logo';
import { BRAND_FALLBACK_LOGOS, BRAND_LOGOS } from '../../components/vehicle/VehicleHero';

const brands = ['Toyota','Honda','Volkswagen','Chevrolet','Fiat','Jeep','Hyundai','BMW','Audi','Ford','Mercedes','Yamaha'];
const rows = [
  ['Dados de mercado real', '✅', '❌', 'Parcial'],
  ['Anúncios ativos', '✅', '❌', '❌'],
  ['Liquidez regional', '✅', '❌', '❌'],
  ['Laudo exportável', '✅', '❌', 'Pago'],
  ['Tendência de preço', '✅', '❌', '❌'],
];

export function LandingPage({ onDemo, loading = false, error = '' }: { onDemo: () => void; loading?: boolean; error?: string }) {
  function start() { localStorage.removeItem('token'); localStorage.removeItem('refresh_token'); onDemo(); }
  return (
    <main className="mcv-premium-page">
      <header className="mcv-premium-header"><Logo /><button onClick={start} disabled={loading}>Avaliar meu veículo</button></header>
      <section className="mcv-premium-hero">
        <div className="mcv-particles" />
        <motion.div className="mcv-premium-copy" initial={{opacity:0,y:18}} animate={{opacity:1,y:0}} transition={{duration:.5}}>
          <p><Sparkles size={16}/> Inteligência automotiva brasileira</p>
          <h1>Descubra o verdadeiro valor do seu veículo</h1>
          <span>Inteligência de mercado real — baseada em anúncios ativos, não em tabelas desatualizadas.</span>
          {error ? <div className="mcv-error"><AlertTriangle size={16}/>{error}</div> : null}
          <div className="mcv-premium-actions"><Button className="shimmer" onClick={start} disabled={loading}>{loading ? <Loader2 className="animate-spin" size={16}/> : null} Avaliar meu veículo agora <ArrowRight size={16}/></Button><a href="#demo">Ver demonstração</a></div>
        </motion.div>
        <motion.aside className="mcv-terminal-card" initial={{opacity:0,scale:.96}} animate={{opacity:1,scale:1}} transition={{duration:.5,delay:.12}}>
          <div><span>Índice MCV™</span><b>87</b></div><h2>R$ 47.800</h2><p>Preço ideal calculado com comparáveis ativos.</p><i/><section><strong>Venda rápida</strong><em>R$ 44.500</em></section><section><strong>Valor premium</strong><em>R$ 51.200</em></section><footer><BadgeCheck size={16}/> Alta liquidez • Mercado favorável</footer>
        </motion.aside>
      </section>

      <section id="demo" className="mcv-premium-section"><Title label="Como funciona" title="Três passos para vender com mais segurança."/><div className="mcv-premium-steps">{[['01','Identifique','Marca, modelo, versão, ano e região.'],['02','Compare','Cruzamento com FIPE local e anúncios ativos.'],['03','Decida','Preço ideal, venda rápida, premium e laudo.']].map((item,i)=><motion.article key={item[0]} initial={{opacity:0,y:20}} whileInView={{opacity:1,y:0}} transition={{delay:i*.1}}><b>{item[0]}</b><h3>{item[1]}</h3><p>{item[2]}</p></motion.article>)}</div></section>
      <section className="mcv-premium-section"><Title label="Por que somos diferentes" title="Mais inteligente que qualquer tabela."/><div className="mcv-compare"><table><thead><tr><th></th><th>Meu Carro Vale</th><th>FIPE Tradicional</th><th>Molicar</th></tr></thead><tbody>{rows.map(r=><tr key={r[0]}><td>{r[0]}</td><td>{r[1]}</td><td>{r[2]}</td><td>{r[3]}</td></tr>)}</tbody></table></div></section>
      <section className="mcv-premium-section"><Title label="Marcas" title="Comece por uma das marcas mais buscadas."/><div className="mcv-brand-grid">{brands.map((brand)=><button key={brand} onClick={start}>{BRAND_LOGOS[brand] ? <img src={BRAND_LOGOS[brand]} alt={brand} onError={(e) => { e.currentTarget.src = BRAND_FALLBACK_LOGOS[brand] || ''; }}/> : <CarFront/>}<span>{brand}</span></button>)}</div></section>
      <footer className="mcv-premium-footer"><Logo/><span>Mais inteligente que qualquer tabela.</span><nav><a href="#demo">Como funciona</a><a href="#avaliacao">Avaliar</a></nav></footer>
    </main>
  );
}
function Title({label,title}:{label:string;title:string}){return <div className="mcv-premium-title"><p>{label}</p><h2>{title}</h2></div>}
