import { useState } from 'react';
import { Car, Lock, Mail, UserRound } from 'lucide-react';

export function AuthPage({ onLogin, onRegister, onDemo, loading, error }: {
  onLogin: (email: string, password: string) => Promise<void>;
  onRegister: (name: string, email: string, password: string, tenantName: string) => Promise<void>;
  onDemo: () => Promise<void>;
  loading: boolean;
  error: string;
}) {
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [name, setName] = useState('');
  const [tenantName, setTenantName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (mode === 'login') await onLogin(email, password);
    else await onRegister(name, email, password, tenantName || name);
  }
  return (
    <main className="mcv-auth-page">
      <section className="mcv-auth-hero">
        <div className="mcv-auth-brand"><Car size={22} /> Meu Carro Vale</div>
        <h1>Consultoria de venda automotiva para pessoas, lojas e concessionárias.</h1>
        <p>Gere laudos, acompanhe veículos, consulte histórico e use dados reais do motor de mercado para negociar melhor.</p>
        <div className="mcv-auth-proof"><span>Multiusuário</span><span>Laudos salvos</span><span>Planos e limites</span><span>Motor de dados real</span></div>
      </section>
      <section className="mcv-auth-card">
        <div className="mcv-auth-tabs"><button type="button" className={mode === 'login' ? 'active' : ''} onClick={() => setMode('login')}>Entrar</button><button type="button" className={mode === 'register' ? 'active' : ''} onClick={() => setMode('register')}>Criar conta</button></div>
        <form onSubmit={submit} className="mcv-auth-form">
          {mode === 'register' && <label><span>Nome</span><div><UserRound size={15}/><input value={name} onChange={(e) => setName(e.target.value)} required placeholder="Seu nome" /></div></label>}
          {mode === 'register' && <label><span>Nome do espaço</span><div><Car size={15}/><input value={tenantName} onChange={(e) => setTenantName(e.target.value)} placeholder="Loja, consultoria ou nome pessoal" /></div></label>}
          <label><span>E-mail</span><div><Mail size={15}/><input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required placeholder="voce@email.com" /></div></label>
          <label><span>Senha</span><div><Lock size={15}/><input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={8} placeholder="Mínimo 8 caracteres" /></div></label>
          {error && <p className="mcv-auth-error">{error}</p>}
          <button className="mcv-primary-action" disabled={loading}>{loading ? 'Processando...' : mode === 'login' ? 'Entrar' : 'Criar conta'}</button>
          <button type="button" className="mcv-secondary-action" onClick={onDemo} disabled={loading}>Abrir modo demonstração</button>
          <p className="mcv-auth-note">Recuperação de senha preparada no backend para conexão futura com provedor de e-mail.</p>
        </form>
      </section>
    </main>
  );
}
