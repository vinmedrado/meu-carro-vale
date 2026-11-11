import { useEffect } from 'react';

export function PricingModal({ open, reason, onClose }: { open: boolean; reason: string; onClose: () => void }) {
  useEffect(() => {
    if (!open) return;
    const onEscape = (event: KeyboardEvent) => { if (event.key === 'Escape') onClose(); };
    window.addEventListener('keydown', onEscape);
    return () => window.removeEventListener('keydown', onEscape);
  }, [open, onClose]);
  if (!open) return null;
  return <div role="presentation" className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
    <section role="dialog" aria-modal="true" aria-labelledby="mcv-pricing-title" className="mcv-muted-panel w-full max-w-md rounded-2xl p-6">
      <h2 id="mcv-pricing-title" className="text-xl font-semibold">Recurso do plano PRO</h2>
      <p className="my-4">{reason}</p>
      <p className="mb-4 text-sm">Consulte os planos da sua conta para verificar os recursos disponíveis.</p>
      <button type="button" onClick={onClose} className="admin-select px-4 py-2">Fechar</button>
    </section>
  </div>;
}
