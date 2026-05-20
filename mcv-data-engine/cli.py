from __future__ import annotations
import argparse
import json
from pathlib import Path
from jobs.pipeline import MCVDataPipeline
from storage.models import init_db


def main():
    parser = argparse.ArgumentParser(description="MCV Data Engine — motor de dados do Meu Carro Vale")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init-db")
    fipe = sub.add_parser("collect-fipe")
    fipe.add_argument("--max-brands", type=int, default=2)
    fipe.add_argument("--max-models-per-brand", type=int, default=2)
    fipe.add_argument("--persist", action="store_true")
    imp = sub.add_parser("import")
    imp.add_argument("path")
    imp.add_argument("--persist", action="store_true")
    batch = sub.add_parser("batch-import")
    batch.add_argument("paths", nargs="+")
    batch.add_argument("--persist", action="store_true")
    sub.add_parser("prepared-collectors")
    args = parser.parse_args()
    pipeline = MCVDataPipeline()
    if args.command == "init-db":
        init_db()
        output = {"status": "ok", "message": "Banco inicializado"}
    elif args.command == "collect-fipe":
        output = pipeline.run_fipe_catalog(args.max_brands, args.max_models_per_brand, args.persist)
    elif args.command == "import":
        output = pipeline.run_import(Path(args.path), persist=args.persist)
    elif args.command == "batch-import":
        output = pipeline.run_batch_import([Path(p) for p in args.paths], persist=args.persist)
    elif args.command == "prepared-collectors":
        output = pipeline.run_prepared_collectors()
    print(json.dumps(output, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
