from __future__ import annotations
from collections import Counter, defaultdict


class MarketQualityAggregator:
    def aggregate(self, records: list[dict]) -> list[dict]:
        groups: dict[tuple, list[dict]] = defaultdict(list)
        for record in records:
            key = (record.get("fonte"), record.get("marca"), record.get("modelo"), record.get("estado"))
            groups[key].append(record)
        rows: list[dict] = []
        for (fonte, marca, modelo, estado), group in groups.items():
            errors = [e for row in group for e in row.get("validation_errors", [])]
            missing = Counter()
            for err in errors:
                if err.startswith("campos_obrigatorios_ausentes:"):
                    for field in err.split(":", 1)[1].split(","):
                        missing[field] += 1
            quality_values = [float(row.get("qualidade_dado") or 0) for row in group]
            rows.append({
                "fonte": fonte,
                "marca": marca,
                "modelo": modelo,
                "estado": estado,
                "total_registros": len(group),
                "qualidade_media": round(sum(quality_values) / max(len(quality_values), 1), 3),
                "registros_com_erro": sum(1 for row in group if row.get("validation_errors")),
                "campos_faltantes": ", ".join(f"{k}:{v}" for k, v in missing.items()) or None,
            })
        return rows
