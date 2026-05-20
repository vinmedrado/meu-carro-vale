from __future__ import annotations
from statistics import median
from typing import Any

from market_behavior.market_velocity_engine import MarketVelocityEngine
from market_behavior.price_pressure_engine import PricePressureEngine
from market_behavior.regional_behavior_engine import RegionalBehaviorEngine
from market_behavior.resistance_engine import ResistanceEngine
from market_behavior.trend_behavior_engine import TrendBehaviorEngine


class MarketBehaviorEngine:
    """Interpreta comportamento de mercado usando comparáveis limpos e snapshots."""

    def __init__(self):
        self.price_pressure = PricePressureEngine()
        self.velocity = MarketVelocityEngine()
        self.resistance = ResistanceEngine()
        self.regional = RegionalBehaviorEngine()
        self.trend = TrendBehaviorEngine()

    def analyze(
        self,
        comparables: list[dict[str, Any]],
        snapshots: list[dict[str, Any]] | None = None,
        target: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        target = target or {}
        target_price = self._target_price(target, comparables)
        pressure = self.price_pressure.analyze(comparables, target_price=target_price)
        velocity = self.velocity.analyze(comparables, snapshots=snapshots)
        resistance = self.resistance.analyze(
            comparables,
            target_price=target_price,
            pressure_score=float(pressure.get("price_pressure_score") or 0),
            velocity_score=float(velocity.get("market_velocity_score") or 0),
        )
        regional = self.regional.analyze(comparables, state=target.get("estado") or target.get("state"), city=target.get("cidade") or target.get("city"))
        trend = self.trend.analyze(snapshots or [])
        stuck = self._stuck_risk(pressure, velocity, resistance)
        summary = self._summary(pressure, velocity, resistance, regional, trend, stuck)
        return {
            **pressure,
            **velocity,
            **resistance,
            **regional,
            **trend,
            **stuck,
            "summary": summary,
            "market_behavior_summary": summary,
            "sample_size": len(comparables),
        }

    def export_rows(self, grouped_inputs: list[dict[str, Any]]) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for item in grouped_inputs:
            target = item.get("target", {})
            behavior = self.analyze(item.get("comparables", []), item.get("snapshots", []), target)
            rows.append({
                "brand": target.get("marca") or target.get("brand"),
                "model": target.get("modelo") or target.get("model"),
                "version": target.get("versao") or target.get("version"),
                "year": target.get("ano") or target.get("year"),
                "state": target.get("estado") or target.get("state"),
                "city": target.get("cidade") or target.get("city"),
                "pressure_level": behavior.get("pressure_level"),
                "velocity_level": behavior.get("velocity_level"),
                "resistance_price": behavior.get("resistance_price"),
                "trend_direction": behavior.get("trend_direction"),
                "stuck_risk_level": behavior.get("stuck_risk_level"),
                "regional_strength": behavior.get("regional_strength"),
                "summary": behavior.get("summary"),
            })
        return rows

    def _target_price(self, target: dict[str, Any], comparables: list[dict[str, Any]]) -> float | None:
        if target.get("preco") is not None:
            return float(target["preco"])
        prices = [float(c["preco"]) for c in comparables if c.get("preco") is not None]
        return float(median(prices)) if prices else None

    def _stuck_risk(self, pressure: dict[str, Any], velocity: dict[str, Any], resistance: dict[str, Any]) -> dict[str, Any]:
        score = round(min(1.0,
            float(pressure.get("price_pressure_score") or 0) * 0.42 +
            (1 - float(velocity.get("market_velocity_score") or 0)) * 0.33 +
            float(resistance.get("stuck_risk_score") or 0) * 0.25
        ), 3)
        if score >= 0.68:
            level = "Alto"
        elif score >= 0.40:
            level = "Moderado"
        else:
            level = "Baixo"
        reason = "Risco calculado por pressão de preço, velocidade de mercado e resistência acima da faixa competitiva."
        return {"stuck_risk_score": score, "stuck_risk_level": level, "stuck_risk_reason": reason}

    def _summary(self, pressure: dict[str, Any], velocity: dict[str, Any], resistance: dict[str, Any], regional: dict[str, Any], trend: dict[str, Any], stuck: dict[str, Any]) -> str:
        if stuck.get("stuck_risk_level") == "Baixo" and velocity.get("market_velocity_score", 0) >= 0.58:
            return "O mercado apresenta boa velocidade e risco baixo de ficar parado quando o preço respeita a faixa dos comparáveis."
        if pressure.get("pressure_level") in {"Pressão alta", "Mercado pressionado"}:
            return "O mercado está pressionado por preço; priorize posicionamento competitivo e use comparáveis recentes para sustentar a negociação."
        if regional.get("regional_strength") == "Região valorizada":
            return "A região informada favorece o modelo, mas o preço ainda deve respeitar o teto de resistência indicado."
        if trend.get("trend_direction") == "Em queda":
            return "A tendência disponível sugere queda de mediana; recomenda-se estratégia conservadora para manter liquidez."
        return "O mercado está equilibrado, com leitura adequada para negociar dentro da faixa recomendada sem perder competitividade."
