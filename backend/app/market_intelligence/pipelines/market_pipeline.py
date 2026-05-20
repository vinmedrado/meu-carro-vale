from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from sqlalchemy.orm import Session
from app.models.market import MarketListing, MarketListingHistory, MarketCollectionJob, MarketSnapshot
from app.market_intelligence.analytics.outliers import is_suspicious_listing
from app.market_intelligence.deduplication.deduplicator import duplicate_score, listing_fingerprint
from app.market_intelligence.normalizers.vehicle_normalizer import normalize_listing

class MarketIngestionPipeline:
    def ingest_rows(self, db: Session, rows: list[dict[str, Any]], source: str, job_id: int | None = None) -> dict[str, int]:
        imported = duplicates = suspicious = errors = 0
        for raw in rows:
            try:
                normalized = normalize_listing(raw, source=source).to_dict()
                if is_suspicious_listing(normalized):
                    suspicious += 1; continue
                existing = db.query(MarketListing).filter(MarketListing.normalized_key == normalized["normalized_key"]).first()
                if existing:
                    decision = duplicate_score(normalized, {c.name: getattr(existing, c.name) for c in MarketListing.__table__.columns if hasattr(existing, c.name)})
                    duplicates += 1
                    try:
                        existing.duplicate_score = max(existing.duplicate_score or 0, decision.duplicate_score)
                    except Exception:
                        pass
                    continue
                item = MarketListing(**{k:v for k,v in normalized.items() if k in MarketListing.__table__.columns.keys()})
                if hasattr(item, "fingerprint"):
                    item.fingerprint = listing_fingerprint(normalized)
                    item.is_active = True
                    item.duplicate_score = 0
                db.add(item); db.flush()
                if 'MarketListingHistory' in globals():
                    db.add(MarketListingHistory(market_listing_id=item.id, price=item.price, mileage=item.mileage, source=item.source, raw=item.raw))
                imported += 1
            except Exception:
                errors += 1
        if job_id:
            job = db.query(MarketCollectionJob).get(job_id)
            if job:
                job.status = "finished"; job.finished_at = datetime.now(timezone.utc); job.imported_count = imported; job.duplicate_count = duplicates; job.error_count = errors + suspicious
        db.commit()
        return {"imported": imported, "duplicates": duplicates, "suspicious": suspicious, "errors": errors}
