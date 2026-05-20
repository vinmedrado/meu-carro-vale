from __future__ import annotations

SCHEDULED_JOBS = [
    {"name": "Atualização FIPE", "cadence": "diária", "enabled": True},
    {"name": "Coleta responsável de mercado", "cadence": "sob demanda/agendada", "enabled": False},
    {"name": "Recalcular liquidez", "cadence": "a cada 6 horas", "enabled": True},
    {"name": "Recalcular estatísticas", "cadence": "a cada 6 horas", "enabled": True},
    {"name": "Limpar duplicados", "cadence": "diária", "enabled": True},
    {"name": "Atualizar comparáveis", "cadence": "após ingestão", "enabled": True},
]
