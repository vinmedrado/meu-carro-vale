from __future__ import annotations
from datetime import date
import pandas as pd


class SnapshotBuilder:
    def build(self, records: list[dict]) -> list[dict]:
        if not records:
            return []
        df = pd.DataFrame(records)
        if "preco" not in df.columns:
            return []
        df = df[df["preco"].notna()]
        if df.empty:
            return []
        df["regiao"] = df.get("estado", "BR").fillna("BR")
        df["semana"] = date.today().isocalendar().week
        df["mes"] = date.today().strftime("%Y-%m")
        group_cols = ["marca", "modelo", "versao", "ano", "regiao"]
        rows: list[dict] = []
        for keys, group in df.groupby(group_cols, dropna=False):
            prices = group["preco"].astype(float)
            median = float(prices.median())
            mean = float(prices.mean())
            p10 = float(prices.quantile(0.10))
            p25 = float(prices.quantile(0.25))
            p75 = float(prices.quantile(0.75))
            p90 = float(prices.quantile(0.90))
            dispersion = float((p75 - p25) / median) if median else 0.0
            temperature = self._temperature(len(group), dispersion)
            rows.append({
                "marca": keys[0], "modelo": keys[1], "versao": keys[2], "ano": int(keys[3]) if pd.notna(keys[3]) else None,
                "regiao": keys[4], "estado": keys[4], "cidade": self._dominant(group, "cidade"),
                "semana": int(group["semana"].iloc[0]), "mes": str(group["mes"].iloc[0]),
                "qtd_anuncios": int(len(group)), "preco_medio": round(mean, 2), "preco_mediano": round(median, 2),
                "preco_p10": round(p10, 2), "preco_p25": round(p25, 2), "preco_p75": round(p75, 2), "preco_p90": round(p90, 2),
                "dispersao_preco": round(dispersion, 4), "liquidez": self._liquidity(len(group), dispersion),
                "temperatura_mercado": temperature,
            })
        return rows

    def _dominant(self, group: pd.DataFrame, column: str) -> str | None:
        if column not in group.columns or group[column].dropna().empty:
            return None
        return str(group[column].dropna().mode().iloc[0])

    def _liquidity(self, volume: int, dispersion: float) -> str:
        if volume >= 30 and dispersion <= 0.12:
            return "Alta"
        if volume >= 12:
            return "Média"
        return "Baixa"

    def _temperature(self, volume: int, dispersion: float) -> str:
        if volume >= 40 and dispersion <= 0.10:
            return "Muito aquecido"
        if volume >= 20 and dispersion <= 0.16:
            return "Aquecido"
        if volume >= 8:
            return "Estável"
        if dispersion > 0.25:
            return "Saturado"
        return "Baixa amostra"
