from __future__ import annotations
import argparse
import json
from pathlib import Path

from pipeline_orchestrator import PipelineOrchestrator


def main() -> None:
    parser = argparse.ArgumentParser(description="Executa o pipeline operacional do mcv-data-engine.")
    parser.add_argument("--input", default="sample_market_listings.csv", help="CSV ou JSON de entrada para ingestão.")
    parser.add_argument("--only", default=None, help="Executa etapa parcial: snapshots, comparables, liquidity, behavior, exports ou final_validation.")
    parser.add_argument("--persist", action="store_true", help="Persiste registros no banco configurado.")
    args = parser.parse_args()
    summary = PipelineOrchestrator().run(input_path=Path(args.input), only=args.only, persist=args.persist)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
