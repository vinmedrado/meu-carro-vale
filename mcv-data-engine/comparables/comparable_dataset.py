from __future__ import annotations
import pandas as pd


class ComparableDatasetBuilder:
    def build(self, records: list[dict], min_quality: float = 0.55) -> pd.DataFrame:
        df = pd.DataFrame(records)
        if df.empty:
            return df
        required = ["preco", "ano", "qualidade_dado"]
        for col in required:
            if col not in df.columns:
                df[col] = None
        df = df[(df["preco"].notna()) & (df["ano"].notna()) & (df["qualidade_dado"] >= min_quality)]
        if df.empty:
            return df
        df["similaridade_base"] = df.apply(self._similarity_base, axis=1)
        df["confianca_comparavel"] = (df["qualidade_dado"].astype(float) * 0.65 + df["similaridade_base"].astype(float) * 0.35).round(3)
        columns = [
            "marca", "modelo", "versao", "ano", "km", "preco", "cidade", "estado", "fonte", "url",
            "combustivel", "cambio", "qualidade_dado", "similaridade_base", "confianca_comparavel",
            "dispersao_grupo", "liquidez_grupo"
        ]
        return df[[c for c in columns if c in df.columns]].copy()

    def enrich_with_group_metrics(self, records: list[dict]) -> list[dict]:
        df = pd.DataFrame(records)
        if df.empty or "preco" not in df.columns:
            return records
        group_cols = [c for c in ["marca", "modelo", "ano", "estado"] if c in df.columns]
        if not group_cols:
            return records
        df["dispersao_grupo"] = 0.0
        df["liquidez_grupo"] = "Baixa"
        for _, idx in df.groupby(group_cols, dropna=False).groups.items():
            group = df.loc[idx]
            prices = group["preco"].dropna().astype(float)
            if prices.empty:
                continue
            median = prices.median()
            dispersion = float((prices.quantile(0.75) - prices.quantile(0.25)) / median) if median else 0.0
            df.loc[idx, "dispersao_grupo"] = round(dispersion, 4)
            df.loc[idx, "liquidez_grupo"] = "Alta" if len(group) >= 20 and dispersion <= 0.15 else "Média" if len(group) >= 8 else "Baixa"
        return df.to_dict(orient="records")

    def _similarity_base(self, row) -> float:
        score = 0.55
        if row.get("versao"):
            score += 0.16
        if row.get("km") is not None:
            score += 0.10
        if row.get("combustivel"):
            score += 0.08
        if row.get("cambio"):
            score += 0.08
        if row.get("cidade"):
            score += 0.03
        return min(round(score, 3), 1.0)
