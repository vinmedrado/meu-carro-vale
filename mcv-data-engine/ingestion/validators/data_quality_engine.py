from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


REQUIRED_FIELDS = ["marca", "modelo", "ano", "preco", "estado", "fonte"]
USEFUL_FIELDS = ["versao", "km", "cidade", "combustivel", "cambio", "url", "vendedor_tipo", "cor"]
VALID_STATES = {
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG", "PA", "PB", "PR",
    "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"
}


@dataclass(slots=True)
class QualityResult:
    quality_score: float
    validation_errors: list[str]
    validation_warnings: list[str]
    normalization_status: str


class DataQualityEngine:
    """Valida anúncios automotivos antes de persistir/exportar.

    A nota é explicável: campos obrigatórios pesam mais, campos úteis refinam a
    confiança e inconsistências automotivas reduzem o resultado.
    """

    def evaluate(self, record: dict[str, Any]) -> QualityResult:
        errors: list[str] = []
        warnings: list[str] = []

        missing_required = [field for field in REQUIRED_FIELDS if not record.get(field)]
        if missing_required:
            errors.append("campos_obrigatorios_ausentes:" + ",".join(missing_required))

        ano = record.get("ano")
        current_year = datetime.now(UTC).year + 1
        if ano is not None and not (1950 <= int(ano) <= current_year):
            errors.append("ano_invalido")

        preco = record.get("preco")
        if preco is not None:
            preco = float(preco)
            if preco <= 1000:
                errors.append("preco_muito_baixo")
            elif preco > 2_000_000:
                warnings.append("preco_muito_alto")

        km = record.get("km")
        if km is not None:
            km = int(km)
            if km < 0:
                errors.append("km_negativa")
            elif km > 500_000:
                warnings.append("km_muito_alta")

        estado = record.get("estado")
        if estado and estado not in VALID_STATES:
            warnings.append("estado_inconsistente")

        if record.get("modelo") and record.get("marca") and str(record["modelo"]).lower() == str(record["marca"]).lower():
            warnings.append("modelo_igual_marca")

        required_score = sum(1 for field in REQUIRED_FIELDS if record.get(field)) / len(REQUIRED_FIELDS)
        useful_score = sum(1 for field in USEFUL_FIELDS if record.get(field)) / len(USEFUL_FIELDS)
        score = (required_score * 0.68) + (useful_score * 0.32)
        score -= len(errors) * 0.12
        score -= len(warnings) * 0.04
        score = max(0.0, min(1.0, round(score, 3)))

        if errors:
            status = "revisar"
        elif score >= 0.82:
            status = "normalizado_alta_confianca"
        elif score >= 0.65:
            status = "normalizado"
        else:
            status = "normalizado_baixa_confianca"

        return QualityResult(score, errors, warnings, status)

    def enrich(self, record: dict[str, Any]) -> dict[str, Any]:
        result = self.evaluate(record)
        enriched = dict(record)
        enriched["qualidade_dado"] = result.quality_score
        enriched["validation_errors"] = result.validation_errors
        enriched["validation_warnings"] = result.validation_warnings
        enriched["normalization_status"] = result.normalization_status
        return enriched
