from __future__ import annotations

from app.market_intelligence.valuation.valuation_engine_v3 import ValuationEngineV3

class RealValuationEngine(ValuationEngineV3):
    """Compatibilidade com a rota atual.

    A implementação real agora vive em market_intelligence/valuation/valuation_engine_v3.py
    para manter a arquitetura plugável sem quebrar imports existentes.
    """
    pass
