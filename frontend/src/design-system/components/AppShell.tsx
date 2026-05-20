import { LogOut, Menu, X } from 'lucide-react';
import { useState } from 'react';
import { Logo } from '../../components/branding/Logo';

const nav = [
  { label: 'Avaliar', href: '#avaliacao' },
  { label: 'Meus Laudos', href: '#meus-laudos' },
  { label: 'Meus Veículos', href: '#meus-veiculos' },
  { label: 'Plano', href: '#plano' },
];

export function AppShell({ children, onLogout }: { children: React.ReactNode; onLogout: () => void }) {
  const [open, setOpen] = useState(false);
  return (
    <main className="mcv-app-clean">
      <header className="mcv-clean-topbar">
        <a className="mcv-clean-brand" href="#avaliacao" aria-label="Meu Carro Vale">
          <Logo />
        </a>
        <nav className="mcv-clean-nav" aria-label="Navegação principal">
          {nav.map((item) => <a key={item.label} href={item.href}>{item.label}</a>)}
          <button onClick={onLogout} className="mcv-clean-logout"><LogOut size={15} /> Sair</button>
        </nav>
        <button className="mcv-mobile-menu-button" onClick={() => setOpen((v) => !v)} aria-label="Abrir menu">
          {open ? <X size={21} /> : <Menu size={21} />}
        </button>
      </header>

      {open ? (
        <nav className="mcv-mobile-menu" aria-label="Menu mobile">
          {nav.map((item) => <a key={item.label} href={item.href} onClick={() => setOpen(false)}>{item.label}</a>)}
          <button onClick={onLogout}>Sair</button>
        </nav>
      ) : null}

      <section className="mcv-clean-workspace">
        {children}
      </section>
    </main>
  );
}
