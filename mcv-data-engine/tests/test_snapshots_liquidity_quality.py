from snapshots.snapshot_builder import SnapshotBuilder
from liquidity.liquidity_calculator import LiquidityCalculator


def test_snapshots_have_evolved_metrics():
    records = [
        {"marca":"Toyota","modelo":"Corolla","versao":"XEI","ano":2020,"preco":100000,"estado":"SP","cidade":"São Paulo"},
        {"marca":"Toyota","modelo":"Corolla","versao":"XEI","ano":2020,"preco":110000,"estado":"SP","cidade":"São Paulo"},
        {"marca":"Toyota","modelo":"Corolla","versao":"XEI","ano":2020,"preco":120000,"estado":"SP","cidade":"São Paulo"},
    ]
    snapshots = SnapshotBuilder().build(records)
    assert snapshots[0]["preco_p10"] > 0
    assert snapshots[0]["temperatura_mercado"]
    liquidity = LiquidityCalculator().calculate(snapshots)
    assert liquidity[0]["velocidade_venda_estimada"]
