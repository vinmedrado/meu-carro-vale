import { Check, Copy, MessageSquareText, X } from "lucide-react";
import type { ValuationResult } from "../../types";
import { fmtCurrency } from "../../lib/format";
import { Button } from "../../components/ui";


export function AdModal({
  open,
  onClose,
  result,
  onCopied,
}: {
  open: boolean;
  onClose: () => void;
  result: ValuationResult;
  onCopied: () => void;
}) {
  const v = result.valuation;
  const title =
    result.ads.title ||
    `${result.vehicle.brand} ${result.vehicle.model} ${result.vehicle.version} ${result.vehicle.year} - avaliação Meu Carro Vale`;
  const description =
    result.ads.webmotors || result.ads.description || result.insights.summary;
  const short =
    result.ads.olx ||
    `${result.vehicle.brand} ${result.vehicle.model} ${result.vehicle.year}, ${result.vehicle.km.toLocaleString("pt-BR")} km, com faixa segura de venda próxima de ${fmtCurrency(v.ideal_price)}.`;
  const highlights = result.insights.strengths.slice(0, 4);

  async function copy(text: string) {
    await navigator.clipboard.writeText(text);
    onCopied();
  }

  if (!open) return null;
  return (
        <div className="modal-backdrop mcv-soft-enter">
          <div className="ad-modal">
            <button
              className="modal-close"
              onClick={onClose}
              aria-label="Fechar"
            >
              <X size={18} />
            </button>
            <span className="report-seal">
              <MessageSquareText size={15} /> Anúncio pronto para copiar
            </span>
            <h3 className="mt-4 text-xl font-semibold tracking-[-0.03em]">
              Texto comercial gerado para venda
            </h3>
            <p className="mt-2 text-sm leading-6 text-ash">
              Use como base para canais de venda, atendimento e negociação.
            </p>
            <div className="mt-6 grid gap-4">
              <AdBlock
                title="Título sugerido"
                text={title}
                onCopy={() => copy(title)}
              />
              <AdBlock
                title="Descrição para venda"
                text={description}
                onCopy={() => copy(description)}
                large
              />
              <AdBlock
                title="Versão curta"
                text={short}
                onCopy={() => copy(short)}
              />
              <div className="rounded-[24px] mcv-muted-panel p-4">
                <div className="flex items-center justify-between gap-3">
                  <h4 className="font-semibold">Destaques do veículo</h4>
                  <Button
                    variant="ghost"
                    onClick={() => copy(highlights.join("\n"))}
                  >
                    <Copy size={15} /> Copiar
                  </Button>
                </div>
                <div className="mt-3 grid gap-2">
                  {highlights.map((item) => (
                    <p
                      key={item}
                      className="rounded-[16px] mcv-muted-panel p-3 text-sm text-ash"
                    >
                      {item}
                    </p>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
  );
}

function AdBlock({
  title,
  text,
  onCopy,
  large = false,
}: {
  title: string;
  text: string;
  onCopy: () => void;
  large?: boolean;
}) {
  return (
    <div className="rounded-[24px] mcv-muted-panel p-4">
      <div className="flex items-center justify-between gap-3">
        <h4 className="font-semibold">{title}</h4>
        <Button variant="ghost" onClick={onCopy}>
          <Copy size={15} /> Copiar
        </Button>
      </div>
      <p
        className={`mt-3 whitespace-pre-line text-sm leading-7 text-ash ${large ? "min-h-24" : ""}`}
      >
        {text}
      </p>
    </div>
  );
}

export function Toast({ message }: { message: string }) {
  if (!message) return null;
  return <div className="mcv-toast mcv-soft-enter"><Check size={17} />{message}</div>;
}
