import type { VehicleInput } from '../types';

export const vehicleSteps = ['Identificação', 'Condição', 'Mercado', 'Fotos', 'Resultado'];

export const loadingLines = [
  'Lendo características comerciais do veículo...',
  'Cruzando FIPE de referência, liquidez e praça regional...',
  'Estimando faixa segura para negociação...',
  'Calculando Potencial Perdido™ e argumento de preço...',
  'Montando laudo profissional...',
];

function demoPhoto(label: string, accent: string) {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="960" height="640" viewBox="0 0 960 640"><defs><linearGradient id="g" x1="0" x2="1" y1="0" y2="1"><stop offset="0" stop-color="#0b0d10"/><stop offset="1" stop-color="#1f232b"/></linearGradient><linearGradient id="a" x1="0" x2="1"><stop offset="0" stop-color="#d7b56d"/><stop offset="1" stop-color="${accent}"/></linearGradient></defs><rect width="960" height="640" rx="42" fill="url(#g)"/><path d="M148 385c24-78 86-130 162-139h236c88 0 169 60 207 139" fill="none" stroke="url(#a)" stroke-width="24" stroke-linecap="round"/><path d="M276 348h390" stroke="#f7f3ea" stroke-width="12" stroke-linecap="round" opacity=".82"/><circle cx="292" cy="420" r="54" fill="#0b0d10" stroke="#d7b56d" stroke-width="14"/><circle cx="668" cy="420" r="54" fill="#0b0d10" stroke="#d7b56d" stroke-width="14"/><text x="64" y="92" fill="#f7f3ea" font-family="Arial, sans-serif" font-size="36" font-weight="700">Meu Carro Vale Demo</text><text x="64" y="140" fill="#a5abb6" font-family="Arial, sans-serif" font-size="24">${label}</text></svg>`;
  return `data:image/svg+xml;utf8,${encodeURIComponent(svg)}`;
}

export const demoVehicles: VehicleInput[] = [
  {
    brand: 'Toyota',
    model: 'Corolla',
    version: 'XEi',
    year: 2021,
    km: 46000,
    transmission: 'Automático',
    fuel: 'Flex',
    color: 'Cinza',
    options: 'multimídia, câmera de ré, piloto automático, chave presencial',
    condition: 'excelente',
    city: 'São Paulo',
    state: 'SP',
    history: 'Uso particular, garagem coberta e baixa exposição urbana.',
    revisions: 'Revisões em concessionária e manual carimbado.',
    notes: 'Veículo com alta liquidez, excelente apresentação e forte procura no mercado regional.',
    photos: [demoPhoto('Toyota Corolla XEi 2021', '#58c7b8'), demoPhoto('Interior bem conservado', '#d7b56d')],
  },
  {
    brand: 'BMW',
    model: '320i',
    version: 'Sport GP',
    year: 2020,
    km: 52000,
    transmission: 'Automático',
    fuel: 'Flex',
    color: 'Branco',
    options: 'teto solar, pacote sport, bancos em couro, sensor dianteiro e traseiro',
    condition: 'bom',
    city: 'Campinas',
    state: 'SP',
    history: 'Perfil de alto padrão, segundo dono e documentação regular.',
    revisions: 'Histórico de revisões organizado.',
    notes: 'Carro de imagem forte, exige bom anúncio e fotos para defender teto de negociação.',
    photos: [demoPhoto('BMW 320i Sport GP', '#8ab4ff'), demoPhoto('Pacote visual sofisticado', '#d7b56d')],
  },
  {
    brand: 'Honda',
    model: 'Civic',
    version: 'Touring',
    year: 2019,
    km: 61000,
    transmission: 'Automático',
    fuel: 'Flex',
    color: 'Preto',
    options: 'turbo, bancos em couro, câmera lateral, assistente de faixa',
    condition: 'excelente',
    city: 'Rio de Janeiro',
    state: 'RJ',
    history: 'Uso familiar e histórico limpo.',
    revisions: 'Revisões preventivas em dia.',
    notes: 'Versão desejada, bom apelo para anúncio e margem saudável sobre proposta conservadora.',
    photos: [demoPhoto('Honda Civic Touring', '#c7a3ff'), demoPhoto('Versão Touring completa', '#d7b56d')],
  },
  {
    brand: 'Jeep',
    model: 'Compass',
    version: 'Limited',
    year: 2022,
    km: 39000,
    transmission: 'Automático',
    fuel: 'Flex',
    color: 'Prata',
    options: 'central multimídia, pacote safety, rodas diamantadas, sensor de chuva',
    condition: 'bom',
    city: 'Curitiba',
    state: 'PR',
    history: 'SUV com bom giro regional e perfil familiar.',
    revisions: 'Revisões registradas e pneus em bom estado.',
    notes: 'Boa percepção de valor, principalmente quando anunciado com laudo visual e fotos claras.',
    photos: [demoPhoto('Jeep Compass Limited', '#7ee787'), demoPhoto('SUV pronto para anúncio', '#d7b56d')],
  },
];

export const initialVehicle: VehicleInput = demoVehicles[0];
