from __future__ import annotations
from dataclasses import dataclass
from typing import Literal


DataType = Literal["string", "integer", "float", "date", "datetime", "boolean"]


@dataclass(frozen=True)
class ColumnContract:
    name: str
    dtype: DataType
    required: bool = True
    min_value: float | None = None
    max_value: float | None = None


@dataclass(frozen=True)
class ExportContract:
    name: str
    schema_version: str
    columns: tuple[ColumnContract, ...]
    primary_columns: tuple[str, ...] = ()


EXPORT_CONTRACTS: dict[str, ExportContract] = {
    "comparables": ExportContract(
        name="comparables",
        schema_version="1.0.0",
        primary_columns=("vehicle_id", "comparable_id"),
        columns=(
            ColumnContract("vehicle_id", "string", False),
            ColumnContract("comparable_id", "string", False),
            ColumnContract("marca", "string"),
            ColumnContract("modelo", "string"),
            ColumnContract("versao", "string", False),
            ColumnContract("ano", "integer", False, 1950, 2100),
            ColumnContract("estado", "string", False),
            ColumnContract("cidade", "string", False),
            ColumnContract("score", "float", False, 0, 100),
            ColumnContract("comparable_score", "float", False, 0, 100),
            ColumnContract("match_quality", "string", False),
            ColumnContract("price_delta", "float", False),
            ColumnContract("km_delta", "float", False),
            ColumnContract("year_delta", "float", False),
            ColumnContract("regional_match", "boolean", False),
            ColumnContract("explanation", "string", False),
            ColumnContract("price_impact", "string", False),
        ),
    ),
    "liquidity": ExportContract(
        name="liquidity",
        schema_version="1.0.0",
        columns=(
            ColumnContract("marca", "string"),
            ColumnContract("modelo", "string"),
            ColumnContract("ano", "integer", False, 1950, 2100),
            ColumnContract("regiao", "string", False),
            ColumnContract("qtd_anuncios", "integer", False, 0),
            ColumnContract("dispersao_preco", "float", False, 0),
            ColumnContract("saturacao", "float", False, 0),
            ColumnContract("pressao_mercado", "float", False, 0),
            ColumnContract("liquidity_level", "string", False),
            ColumnContract("temperatura_mercado", "string", False),
        ),
    ),
    "market_behavior": ExportContract(
        name="market_behavior",
        schema_version="1.0.0",
        columns=(
            ColumnContract("brand", "string", False),
            ColumnContract("model", "string", False),
            ColumnContract("version", "string", False),
            ColumnContract("year", "integer", False, 1950, 2100),
            ColumnContract("state", "string", False),
            ColumnContract("city", "string", False),
            ColumnContract("pressure_level", "string", False),
            ColumnContract("velocity_level", "string", False),
            ColumnContract("resistance_price", "float", False, 0),
            ColumnContract("trend_direction", "string", False),
            ColumnContract("stuck_risk_level", "string", False),
            ColumnContract("regional_strength", "string", False),
            ColumnContract("summary", "string", False),
        ),
    ),
    "snapshots": ExportContract(
        name="snapshots",
        schema_version="1.0.0",
        columns=(
            ColumnContract("marca", "string"),
            ColumnContract("modelo", "string"),
            ColumnContract("versao", "string", False),
            ColumnContract("ano", "integer", False, 1950, 2100),
            ColumnContract("regiao", "string", False),
            ColumnContract("qtd_anuncios", "integer", False, 0),
            ColumnContract("preco_mediano", "float", False, 0),
            ColumnContract("preco_p25", "float", False, 0),
            ColumnContract("preco_p75", "float", False, 0),
            ColumnContract("dispersao_preco", "float", False, 0),
            ColumnContract("liquidez", "string", False),
            ColumnContract("temperatura_mercado", "string", False),
        ),
    ),
    "catalog": ExportContract(
        name="catalog",
        schema_version="1.0.0",
        columns=(
            ColumnContract("marca", "string"),
            ColumnContract("modelo", "string"),
            ColumnContract("versao", "string", False),
            ColumnContract("ano", "integer", False, 1950, 2100),
            ColumnContract("codigo_fipe", "string", False),
            ColumnContract("preco_fipe", "float", False, 0),
        ),
    ),
    "normalized_catalog": ExportContract(
        name="normalized_catalog",
        schema_version="1.0.0",
        columns=(
            ColumnContract("marca", "string"),
            ColumnContract("modelo", "string"),
            ColumnContract("versao", "string", False),
            ColumnContract("ano", "integer", False, 1950, 2100),
            ColumnContract("preco", "float", False, 0),
            ColumnContract("qualidade_dado", "float", False, 0, 1),
            ColumnContract("normalizado", "boolean", False),
        ),
    ),
}


def get_contract(name: str) -> ExportContract | None:
    return EXPORT_CONTRACTS.get(name)


def contract_names() -> list[str]:
    return sorted(EXPORT_CONTRACTS)
