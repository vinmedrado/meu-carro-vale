from __future__ import annotations

from fastapi import APIRouter, Query

from app.services.data_engine_client import MCVDataEngineClient

router = APIRouter(prefix="/search", tags=["busca"])


@router.get("/vehicles")
def search_vehicles(q: str = Query(..., min_length=2), limit: int = Query(10, ge=1, le=20)):
    """Busca viva de veículos usando o catálogo oficial do mcv-data-engine.

    Quando a API do motor de dados estiver fora, o cliente tenta os exports locais.
    Se não houver dado real disponível, retorna lista vazia sem inventar resultado.
    """
    client = MCVDataEngineClient()
    return client.search_catalog(q, limit=limit)
