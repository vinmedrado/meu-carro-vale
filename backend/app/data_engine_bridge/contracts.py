from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class ExportContract:
    name: str
    required_columns: tuple[str, ...]
    numeric_columns: tuple[str, ...] = ()


EXPORT_CONTRACTS: dict[str, ExportContract] = {
    "comparables": ExportContract(
        name="comparables",
        required_columns=(
            "marca", "modelo", "ano", "estado", "preco_base", "preco_comparavel",
            "km_base", "km_comparavel", "comparable_score", "match_quality",
            "price_delta", "km_delta", "year_delta", "regional_match", "explanation", "price_impact",
        ),
        numeric_columns=("ano", "preco_base", "preco_comparavel", "km_base", "km_comparavel", "comparable_score", "price_delta", "km_delta", "year_delta"),
    ),
    "liquidity": ExportContract(
        name="liquidity",
        required_columns=("marca", "modelo", "ano", "regiao", "qtd_anuncios", "dispersao_preco", "pressao_mercado", "temperatura_mercado", "liquidity_level"),
        numeric_columns=("ano", "qtd_anuncios", "dispersao_preco", "pressao_mercado"),
    ),
    "market_behavior": ExportContract(
        name="market_behavior",
        required_columns=("brand", "model", "year", "state", "pressure_level", "velocity_level", "resistance_price", "trend_direction", "stuck_risk_level", "summary"),
        numeric_columns=("year", "resistance_price"),
    ),
    "snapshots": ExportContract(
        name="snapshots",
        required_columns=("marca", "modelo", "ano", "estado", "qtd_anuncios", "preco_mediano", "preco_p25", "preco_p75", "dispersao_preco", "liquidez", "temperatura_mercado"),
        numeric_columns=("ano", "qtd_anuncios", "preco_mediano", "preco_p25", "preco_p75", "dispersao_preco"),
    ),
}


def missing_columns(columns: Iterable[str], contract: ExportContract) -> list[str]:
    existing = {str(c) for c in columns}
    return [col for col in contract.required_columns if col not in existing]
