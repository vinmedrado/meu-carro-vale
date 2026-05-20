import { CarFront } from 'lucide-react';

export function Logo({ compact = false }: { compact?: boolean }) {
  return (
    <div className="mcv-brand flex items-center gap-3">
      <div className="logo-mark">
        <CarFront size={20} />
      </div>
      {!compact && (
        <div className="leading-tight">
          <div className="text-sm font-semibold tracking-[-0.02em] mcv-text">Meu Carro Vale</div>
          <div className="text-[10px] uppercase tracking-[0.18em] text-ash">Avaliação automotiva</div>
        </div>
      )}
    </div>
  );
}
