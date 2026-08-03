import type { VehicleInput } from '../types';

export const vehicleSteps = ['Identificação', 'Condição', 'Mercado', 'Fotos', 'Resultado'];

export const loadingLines = [
  'Lendo características comerciais do veículo...',
  'Cruzando FIPE de referência, liquidez e praça regional...',
  'Estimando faixa segura para negociação...',
  'Calculando Potencial Perdido™ e argumento de preço...',
  'Montando laudo profissional...',
];

export function demoPhoto(label: string, accent: string) {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="960" height="640" viewBox="0 0 960 640"><defs><linearGradient id="g" x1="0" x2="1" y1="0" y2="1"><stop offset="0" stop-color="#F8FAFC"/><stop offset="1" stop-color="#E8F3EF"/></linearGradient><linearGradient id="a" x1="0" x2="1"><stop offset="0" stop-color="${accent}"/><stop offset="1" stop-color="#d7b56d"/></linearGradient></defs><rect width="960" height="640" rx="42" fill="url(#g)"/><ellipse cx="480" cy="504" rx="320" ry="32" fill="#D0D5DD" opacity=".5"/><path d="M138 402c18-82 91-142 179-142h226c105 0 201 55 256 142l42 2c34 2 63 28 69 62l6 36H44l8-40c8-34 37-58 72-60h14z" fill="url(#a)"/><path d="M330 280h217c58 0 112 30 145 80H258c15-48 39-80 72-80z" fill="#fff" opacity=".84"/><path d="M378 296h78v64H282c16-30 48-58 96-64zM478 296h68c43 0 80 21 111 64H478z" fill="#d9eef7"/><circle cx="280" cy="488" r="62" fill="#101828"/><circle cx="280" cy="488" r="32" fill="#F2F4F7"/><circle cx="702" cy="488" r="62" fill="#101828"/><circle cx="702" cy="488" r="32" fill="#F2F4F7"/><rect x="670" y="410" width="92" height="18" rx="9" fill="#fff" opacity=".74"/><text x="64" y="92" fill="#101828" font-family="Arial, sans-serif" font-size="36" font-weight="800">Meu Carro Vale Demo</text><text x="64" y="140" fill="#667085" font-family="Arial, sans-serif" font-size="24" font-weight="700">${label}</text></svg>`;
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
