import { useState } from "react";
import { demoPhoto, demoVehicles, initialVehicle } from "../data/vehicleDefaults";
import {
  autoValuateVehicle,
  loginDemo,
  loginUser,
  PORTFOLIO_MODE,
  registerUser,
  valuateVehicle,
} from "../lib/api";
import type { ValuationResult, VehicleInput } from "../types";

export function useValuationFlow() {
  const [token, setToken] = useState(localStorage.getItem("token") || "");
  const [vehicle, setVehicle] = useState<VehicleInput>(initialVehicle);
  const [result, setResult] = useState<ValuationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  function persistSession(data: any) {
    localStorage.setItem("token", data.access_token);
    localStorage.setItem("refresh_token", data.refresh_token);
    setToken(data.access_token);
  }

  function buildPortfolioResult(input: VehicleInput): ValuationResult {
    const vehicleLabel = `${input.brand || "Chevrolet"} ${input.model || "Agile"} ${input.version || "LTZ 1.4 Flex"} ${input.year || 2013}`.trim();
    const km = Number(input.km || 82000);
    const fipe = 37200;
    const recommended = Math.round(fipe * 1.045);
    const quick = Math.round(recommended * 0.94);
    const premium = Math.round(recommended * 1.052);
    const heroImage = input.photos?.[0] || demoPhoto(vehicleLabel, "#166F52");
    return {
      vehicle: {
        brand: input.brand || "Chevrolet",
        model: input.model || "Agile",
        version: input.version || "LTZ 1.4 Flex",
        year: Number(input.year || 2013),
        km,
        city: input.city || "São Paulo",
        state: input.state || "SP",
      },
      customer_valuation: {
        vehicle_label: vehicleLabel,
        fipe_price: fipe,
        market_price_estimate: recommended,
        quick_sale_price: quick,
        recommended_price: recommended,
        premium_sale_price: premium,
        confidence_score: 82,
        liquidity_score: 78,
        comparable_count: 12,
        market_sources: ["Mercado demonstrativo"],
        human_summary: "Seu veículo está com boa liquidez e preço alinhado ao mercado. A análise indica uma faixa segura para anunciar e negociar.",
        liquidity_level: "alta",
        confidence_level: "alta",
        market_stability: "estável",
        valuation_insights: [
          "O veículo apresenta boa liquidez no mercado atual.",
          "Há consistência entre os anúncios comparáveis.",
          "A faixa recomendada preserva margem de negociação.",
        ],
      },
      valuation: {
        fipe_simulated: fipe,
        fipe_price: fipe,
        market_price_estimate: recommended,
        quick_sale_price: quick,
        recommended_price: recommended,
        ideal_price: recommended,
        premium_sale_price: premium,
        recommended_top_price: premium,
        confidence_score: 82,
        liquidity_score: 78,
        comparable_count: 12,
        market_sources: ["Mercado demonstrativo"],
        human_summary: "Seu veículo está com boa liquidez e preço alinhado ao mercado. A análise indica uma faixa segura para anunciar e negociar.",
        market_reference: recommended,
        negotiation_range: [quick, premium],
        vehicle_score: 84,
        attractiveness_score: 80,
        chart: [],
        liquidity_curve: [],
      },
      insights: {
        summary: "Análise pronta para negociação.",
      },
    } as any;
  }

  async function login(email: string, password: string) {
    setError("");
    setLoading(true);
    try {
      const data = await loginUser(email, password);
      persistSession(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Não foi possível entrar");
    } finally {
      setLoading(false);
    }
  }

  async function register(
    name: string,
    email: string,
    password: string,
    tenantName: string,
  ) {
    setError("");
    setLoading(true);
    try {
      const data = await registerUser(name, email, password, tenantName);
      persistSession(data);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Não foi possível criar a conta",
      );
    } finally {
      setLoading(false);
    }
  }

  async function enterDemo() {
    setError("");
    setLoading(true);

    const demonstraçãoVehicle = demoVehicles[0];
    setVehicle(demonstraçãoVehicle);

    try {
      const data = await loginDemo();
      persistSession(data);

      setResult({
        vehicle: {
          brand: "Chevrolet",
          model: "Agile",
          version: "LTZ 1.4 Flex",
          year: 2013,
          km: 82000,
          city: "São Paulo",
          state: "SP",
        },
        customer_valuation: {
          vehicle_label: "Chevrolet Agile LTZ 1.4 Flex 2013",
          fipe_price: 37200,
          market_price_estimate: 38900,
          quick_sale_price: 36500,
          recommended_price: 38900,
          premium_sale_price: 40900,
          confidence_score: 82,
          liquidity_score: 78,
          comparable_count: 12,
          market_sources: ["Mercado importado"],
          quarter: "2026Q2",
          state: "SP",
          generated_at: new Date().toISOString(),
          human_summary:
            "Seu veículo está com boa liquidez e preço alinhado ao mercado. A análise indica uma faixa segura para anunciar e negociar.",
          pricing_strategy: [
            {
              label: "Venda rápida",
              value: 36500,
              description:
                "Faixa mais competitiva para atrair interessados mais rápido.",
              when_to_use: "Use quando a prioridade for vender em menos tempo.",
            },
            {
              label: "Preço recomendado",
              value: 38900,
              description:
                "Equilíbrio entre atratividade, margem de negociação e valor percebido.",
              when_to_use: "Use como preço principal do anúncio.",
            },
            {
              label: "Preço premium",
              value: 40900,
              description:
                "Faixa mais alta para veículos muito bem conservados.",
              when_to_use: "Use quando não houver pressa.",
            },
          ],
          liquidity_level: "alta",
          confidence_level: "alta",
          market_stability: "estável",
          valuation_insights: [
            "O veículo apresenta boa liquidez no mercado atual.",
            "Há forte consistência entre os anúncios comparáveis.",
            "O mercado demonstra estabilidade para este modelo.",
          ],
        },
        valuation: {
          fipe_simulated: 37200,
          fipe_price: 37200,
          market_price_estimate: 38900,
          quick_sale_price: 36500,
          recommended_price: 38900,
          ideal_price: 38900,
          premium_sale_price: 40900,
          recommended_top_price: 40900,
          confidence_score: 82,
          liquidity_score: 78,
          comparable_count: 12,
          market_sources: ["Mercado importado"],
          human_summary:
            "Seu veículo está com boa liquidez e preço alinhado ao mercado. A análise indica uma faixa segura para anunciar e negociar.",
          pricing_strategy: [
            {
              label: "Venda rápida",
              value: 36500,
              description:
                "Faixa mais competitiva para atrair interessados mais rápido.",
              when_to_use: "Use quando a prioridade for vender em menos tempo.",
            },
            {
              label: "Preço recomendado",
              value: 38900,
              description:
                "Equilíbrio entre atratividade, margem de negociação e valor percebido.",
              when_to_use: "Use como preço principal do anúncio.",
            },
            {
              label: "Preço premium",
              value: 40900,
              description:
                "Faixa mais alta para veículos muito bem conservados.",
              when_to_use: "Use quando não houver pressa.",
            },
          ],
          market_reference: 38900,
          negotiation_range: [36500, 40900],
          vehicle_score: 84,
          attractiveness_score: 80,
          market_delta_vs_fipe_pct: 4.6,
          chart: [],
          liquidity_curve: [],
        },
        liquidity: {
          level: "Alta",
          estimated_days: 18,
        },
        strategy: {
          summary: "Mercado aquecido para hatch compacto automático.",
        },
      } as any);
    } catch (err) {
      console.error(err);
      localStorage.removeItem("token");
      setToken("");
      setResult(null);
      setError(
        err instanceof Error
          ? err.message
          : "O backend não respondeu. Confira se ele está rodando em http://127.0.0.1:8020",
      );
    } finally {
      setLoading(false);
    }
  }

  async function generateValuation(vehicleOverride?: VehicleInput) {
    setLoading(true);
    setError("");
    try {
      const sourceVehicle = vehicleOverride || vehicle;
      const safeVehicle = {
        ...sourceVehicle,
        city: String(sourceVehicle.city || "").trim() || "Não informado",
        state: String(sourceVehicle.state || "")
          .trim()
          .toUpperCase(),
        condition: String(sourceVehicle.condition || "").trim() || "Bom",
        transmission: String(sourceVehicle.transmission || "").trim() || "Automático",
        fuel: String(sourceVehicle.fuel || "").trim() || "Flex",
        color: String(sourceVehicle.color || "").trim() || "Não informado",
      };
      const query = String(safeVehicle.query || "").trim();
      if (PORTFOLIO_MODE) {
        setResult(buildPortfolioResult(safeVehicle));
        return;
      }
      if (query) {
        const data = await autoValuateVehicle(token, {
          query,
          mileage: Number(safeVehicle.km || 0),
          state: safeVehicle.state,
          city: safeVehicle.city,
          condition: safeVehicle.condition,
          brand: safeVehicle.brand,
          model: safeVehicle.model,
          version: safeVehicle.version,
          year: safeVehicle.year,
          transmission: safeVehicle.transmission,
          fuel: safeVehicle.fuel,
          color: safeVehicle.color,
          options: safeVehicle.options,
          history: safeVehicle.history,
          revisions: safeVehicle.revisions,
        });
        setResult(data);
      } else {
        const data = await valuateVehicle(token, safeVehicle);
        setResult(data);
      }
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Não foi possível concluir a análise",
      );
    } finally {
      setLoading(false);
    }
  }

  function logout() {
    localStorage.removeItem("token");
    localStorage.removeItem("refresh_token");
    setToken("");
    setResult(null);
    setVehicle(initialVehicle);
  }

  return {
    token,
    vehicle,
    setVehicle,
    result,
    loading,
    error,
    login,
    register,
    enterDemo,
    generateValuation,
    logout,
  };
}
