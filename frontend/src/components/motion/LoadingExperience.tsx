const lines = [
  'Lendo referências da praça informada...',
  'Organizando comparáveis semelhantes...',
  'Calculando faixa recomendada...',
  'Preparando laudo profissional...',
];

export function LoadingExperience({ title = 'Analisando seu veículo...', fullScreen = false }: { title?: string; fullScreen?: boolean }) {
  const content = (
    <div className="loading-cinematic">
      <div className="loading-ring"><span /></div>
      <div>
        <p className="eyebrow">Meu Carro Vale</p>
        <h2 className="mt-2 text-xl font-semibold tracking-[-0.03em]">{title}</h2>
        <div className="mt-5 grid gap-2">
          {lines.map((line) => (
            <div key={line} className="mcv-loading-line">
              <span />{line}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
  if (!fullScreen) return content;
  return <main className="grid min-h-screen place-items-center mcv-app-bg p-6 mcv-text">{content}</main>;
}
