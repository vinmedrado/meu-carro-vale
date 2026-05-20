import { Loader2, Search } from 'lucide-react';
import { useEffect, useState } from 'react';
import { searchVehicles, type VehicleSuggestion } from '../../lib/api';

export function VehicleSearchBox({ onSelect }: { onSelect: (suggestion: VehicleSuggestion, query: string) => void }) {
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState<VehicleSuggestion[]>([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    const q = query.trim();
    if (q.length < 2) { setSuggestions([]); setMessage(''); return; }
    const timer = window.setTimeout(async () => {
      setLoading(true); setMessage('');
      try {
        const data = await searchVehicles(q);
        setSuggestions(data);
        if (!data.length) setMessage('Nenhum veículo encontrado.');
      } catch (err) {
        setSuggestions([]);
        setMessage(err instanceof Error ? err.message : 'Busca indisponível.');
      } finally { setLoading(false); }
    }, 320);
    return () => window.clearTimeout(timer);
  }, [query]);

  return (
    <div className="mcv-live-search-clean">
      <div className="mcv-search-box-clean">
        <Search size={20} />
        <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Digite modelo, versão ou ano" />
        {loading ? <Loader2 className="animate-spin" size={18} /> : null}
      </div>
      <p className="mcv-search-example">Exemplo: Agile LTZ 2013</p>
      {message ? <p className="mcv-search-message-clean">{message}</p> : null}
      {suggestions.length ? (
        <div className="mcv-search-suggestions-clean">
          {suggestions.slice(0, 6).map((item, index) => (
            <button key={`${item.display_name}-${index}`} type="button" onClick={() => onSelect(item, query)}>
              <strong>{item.display_name}</strong>
              <span>{item.fipe_code ? `FIPE ${item.fipe_code}` : 'Catálogo'} • {item.confidence}%</span>
            </button>
          ))}
        </div>
      ) : null}
    </div>
  );
}
