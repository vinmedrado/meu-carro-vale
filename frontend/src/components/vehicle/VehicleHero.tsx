import { CarFront } from 'lucide-react';

function svgData(svg: string) {
  return `data:image/svg+xml;utf8,${encodeURIComponent(svg)}`;
}

function logo(label: string, accent = '#166F52') {
  const initials = label
    .split(/\s+/)
    .map((part) => part[0])
    .join('')
    .slice(0, 2)
    .toUpperCase();
  return svgData(`<svg xmlns="http://www.w3.org/2000/svg" width="160" height="96" viewBox="0 0 160 96"><rect width="160" height="96" rx="24" fill="#fff"/><rect x="1.5" y="1.5" width="157" height="93" rx="22.5" fill="none" stroke="#E4E7EC" stroke-width="3"/><circle cx="80" cy="42" r="25" fill="#F2F4F7"/><text x="80" y="51" text-anchor="middle" font-family="Arial, sans-serif" font-size="24" font-weight="800" fill="${accent}">${initials}</text><text x="80" y="78" text-anchor="middle" font-family="Arial, sans-serif" font-size="16" font-weight="700" fill="#475467">${label}</text></svg>`);
}

export const BRAND_FALLBACK_LOGOS: Record<string, string> = {
  Toyota: logo('Toyota', '#C1121F'),
  Honda: logo('Honda', '#B42318'),
  Volkswagen: logo('VW', '#1456F0'),
  Chevrolet: logo('Chevrolet', '#B8871D'),
  Fiat: logo('Fiat', '#9E1B32'),
  Jeep: logo('Jeep', '#166F52'),
  Ford: logo('Ford', '#1456F0'),
  Hyundai: logo('Hyundai', '#344054'),
  BMW: logo('BMW', '#1456F0'),
  Mercedes: logo('Mercedes', '#101828'),
  Yamaha: logo('Yamaha', '#B42318'),
  Renault: logo('Renault', '#B8871D'),
};

export const BRAND_LOGOS: Record<string, string> = {
  Toyota: 'https://cdn.jsdelivr.net/npm/simple-icons@latest/icons/toyota.svg',
  Honda: 'https://cdn.jsdelivr.net/npm/simple-icons@latest/icons/honda.svg',
  Volkswagen: 'https://cdn.jsdelivr.net/npm/simple-icons@latest/icons/volkswagen.svg',
  Chevrolet: 'https://cdn.jsdelivr.net/npm/simple-icons@latest/icons/chevrolet.svg',
  Fiat: 'https://cdn.jsdelivr.net/npm/simple-icons@latest/icons/fiat.svg',
  Jeep: 'https://cdn.jsdelivr.net/npm/simple-icons@latest/icons/jeep.svg',
  Ford: 'https://cdn.jsdelivr.net/npm/simple-icons@latest/icons/ford.svg',
  Hyundai: 'https://cdn.jsdelivr.net/npm/simple-icons@latest/icons/hyundai.svg',
  BMW: 'https://cdn.jsdelivr.net/npm/simple-icons@latest/icons/bmw.svg',
  Mercedes: 'https://cdn.jsdelivr.net/npm/simple-icons@latest/icons/mercedes.svg',
  Yamaha: 'https://cdn.jsdelivr.net/npm/simple-icons@latest/icons/yamahamotorcorporation.svg',
  Renault: 'https://cdn.jsdelivr.net/npm/simple-icons@latest/icons/renault.svg',
};

export interface VehicleHeroProps { brand: string; model: string; year: number; imageUrl?: string; }

export function VehicleHero({ brand, model, year, imageUrl }: VehicleHeroProps) {
  const logo = BRAND_LOGOS[brand];
  const fallback = demoCarImage(`${brand} ${model}`, '#166F52');
  return (
    <article className="mcv-vehicle-hero-premium">
      <img src={imageUrl || fallback} alt={`${brand} ${model}`} onError={(e) => { e.currentTarget.src = fallback; }} />
      <div className="mcv-vehicle-hero-fallback"><CarFront size={54}/></div>
      <div className="mcv-vehicle-hero-overlay">
        {logo ? <img src={logo} alt={brand} onError={(e) => { e.currentTarget.src = BRAND_FALLBACK_LOGOS[brand] || ''; }} /> : <CarFront size={24} />}
        <strong>{brand} {model}</strong>
        <span>{year}</span>
      </div>
    </article>
  );
}

export function demoCarImage(label: string, accent = '#166F52') {
  return svgData(`<svg xmlns="http://www.w3.org/2000/svg" width="960" height="540" viewBox="0 0 960 540"><defs><linearGradient id="bg" x1="0" x2="1" y1="0" y2="1"><stop offset="0" stop-color="#F8FAFC"/><stop offset="1" stop-color="#E8F3EF"/></linearGradient><linearGradient id="car" x1="0" x2="1"><stop offset="0" stop-color="${accent}"/><stop offset="1" stop-color="#D8A83F"/></linearGradient></defs><rect width="960" height="540" rx="34" fill="url(#bg)"/><ellipse cx="480" cy="438" rx="310" ry="30" fill="#D0D5DD" opacity=".45"/><path d="M179 341c18-74 84-128 164-128h196c96 0 184 49 234 128l38 1c30 2 55 25 60 55l5 31H94l7-35c7-30 33-51 64-52h14z" fill="url(#car)"/><path d="M316 231h215c55 0 108 28 139 75H254c14-45 34-75 62-75z" fill="#FFFFFF" opacity=".82"/><path d="M367 244h75v62H276c15-28 45-56 91-62zM462 244h67c41 0 76 20 104 62H462z" fill="#D9EEF7"/><rect x="124" y="365" width="712" height="48" rx="24" fill="#101828" opacity=".12"/><circle cx="271" cy="414" r="61" fill="#101828"/><circle cx="271" cy="414" r="31" fill="#F2F4F7"/><circle cx="690" cy="414" r="61" fill="#101828"/><circle cx="690" cy="414" r="31" fill="#F2F4F7"/><rect x="662" y="344" width="94" height="18" rx="9" fill="#FFFFFF" opacity=".72"/><rect x="164" y="344" width="72" height="18" rx="9" fill="#FFF7D6"/><text x="52" y="70" font-family="Arial, sans-serif" font-size="24" font-weight="800" fill="#101828">Meu Carro Vale</text><text x="52" y="104" font-family="Arial, sans-serif" font-size="20" font-weight="700" fill="#667085">${label}</text></svg>`);
}
