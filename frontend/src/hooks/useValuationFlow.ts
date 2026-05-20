import { useState } from 'react';
import { demoVehicles, initialVehicle } from '../data/vehicleDefaults';
import { autoValuateVehicle, loginDemo, loginUser, registerUser, valuateVehicle } from '../lib/api';
import type { ValuationResult, VehicleInput } from '../types';

export function useValuationFlow() {
  const [token, setToken] = useState(localStorage.getItem('token') || '');
  const [vehicle, setVehicle] = useState<VehicleInput>(initialVehicle);
  const [result, setResult] = useState<ValuationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  function persistSession(data: any) {
    localStorage.setItem('token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
    setToken(data.access_token);
  }

  async function login(email: string, password: string) {
    setError(''); setLoading(true);
    try { const data = await loginUser(email, password); persistSession(data); }
    catch (err) { setError(err instanceof Error ? err.message : 'Não foi possível entrar'); }
    finally { setLoading(false); }
  }

  async function register(name: string, email: string, password: string, tenantName: string) {
    setError(''); setLoading(true);
    try { const data = await registerUser(name, email, password, tenantName); persistSession(data); }
    catch (err) { setError(err instanceof Error ? err.message : 'Não foi possível criar a conta'); }
    finally { setLoading(false); }
  }

  async function enterDemo() {
    setError('');
    setLoading(true);

    const demonstraçãoVehicle = demoVehicles[0];
    setVehicle(demonstraçãoVehicle);

    try {
      const data = await loginDemo();
      persistSession(data);

      setResult({
        vehicle: {
          brand: 'Chevrolet',
          model: 'Agile',
          version: 'LTZ 1.4 Flex',
          year: 2013,
        },
        valuation: {
          recommended_price: 38900,
          announce_price: 40900,
          minimum_price: 37200,
        },
        liquidity: {
          level: 'Alta',
          estimated_days: 18,
        },
        strategy: {
          summary: 'Mercado aquecido para hatch compacto automático.',
        },
      } as any);
    } catch (err) {
      console.error(err);
      localStorage.removeItem('token');
      setToken('');
      setResult(null);
      setError(err instanceof Error ? err.message : 'O backend não respondeu. Confira se ele está rodando em http://127.0.0.1:8010');
    } finally {
      setLoading(false);
    }
  }

  async function generateValuation() {
    setLoading(true);
    setError('');
    try {
      const query = String(vehicle.query || '').trim();
      if (query) {
        const data = await autoValuateVehicle(token, {
          query,
          mileage: Number(vehicle.km || 0),
          state: vehicle.state,
          city: vehicle.city,
          condition: vehicle.condition,
          brand: vehicle.brand,
          model: vehicle.model,
          version: vehicle.version,
          year: vehicle.year,
          transmission: vehicle.transmission,
          fuel: vehicle.fuel,
          color: vehicle.color,
          options: vehicle.options,
          history: vehicle.history,
          revisions: vehicle.revisions,
        });
        setResult(data);
      } else {
        const data = await valuateVehicle(token, vehicle);
        setResult(data);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Não foi possível concluir a análise');
    } finally {
      setLoading(false);
    }
  }

  function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('refresh_token');
    setToken('');
    setResult(null);
    setVehicle(initialVehicle);
  }

  return { token, vehicle, setVehicle, result, loading, error, login, register, enterDemo, generateValuation, logout };
}
