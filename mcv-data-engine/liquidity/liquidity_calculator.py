from __future__ import annotations


class LiquidityCalculator:
    def calculate(self, snapshots: list[dict]) -> list[dict]:
        results = []
        for s in snapshots:
            volume = int(s.get("qtd_anuncios", 0) or 0)
            dispersion = float(s.get("dispersao_preco") or 0)
            saturation = min(volume / 90, 1.0)
            stability = max(0.0, 1 - min(dispersion / 0.35, 1.0))
            regional_volume = min(volume / 35, 1.0)
            pressure = round((dispersion * 0.42) + (saturation * 0.33) + ((1 - stability) * 0.25), 3)
            sale_velocity = self._sale_velocity(volume, dispersion)
            level = self._level(volume, dispersion)
            results.append({
                **{k: s.get(k) for k in ["marca", "modelo", "ano", "regiao"]},
                "qtd_anuncios": volume,
                "dispersao_preco": dispersion,
                "saturacao": round(saturation, 3),
                "pressao_mercado": pressure,
                "volume_regional": round(regional_volume, 3),
                "estabilidade": round(stability, 3),
                "velocidade_venda_estimada": sale_velocity,
                "tendencia": self._trend(volume, dispersion, pressure),
                "temperatura_mercado": s.get("temperatura_mercado"),
                "liquidity_level": level,
            })
        return results

    def _level(self, volume: int, dispersion: float) -> str:
        if volume >= 35 and dispersion <= 0.12:
            return "Muito Alta"
        if volume >= 20 and dispersion <= 0.18:
            return "Alta"
        if volume >= 8:
            return "Média"
        return "Baixa"

    def _sale_velocity(self, volume: int, dispersion: float) -> str:
        if volume >= 35 and dispersion <= 0.12:
            return "10 a 18 dias"
        if volume >= 20:
            return "18 a 30 dias"
        if volume >= 8:
            return "30 a 45 dias"
        return "acima de 45 dias"

    def _trend(self, volume: int, dispersion: float, pressure: float) -> str:
        if volume >= 30 and pressure <= 0.25:
            return "mercado líquido"
        if dispersion > 0.22:
            return "preços dispersos"
        if volume < 8:
            return "baixa amostra"
        return "mercado estável"
