from __future__ import annotations
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.vehicle_catalog.aliases.brand_aliases import BRAND_ALIASES
from app.vehicle_catalog.aliases.model_aliases import MODEL_ALIASES
from app.vehicle_catalog.models import VehicleBrand, VehicleBrandAlias, VehicleModel, VehicleModelAlias, VehicleVersion
from app.vehicle_catalog.normalizers.catalog_normalizer import CatalogMatchResult, clean_text, model_alias_index, normalize_brand_name, normalize_model_name, similarity

class VehicleCatalogService:
    def ensure_brand(self, db: Session, vehicle_type: str, fipe_code: str, name: str) -> VehicleBrand:
        canonical = normalize_brand_name(name) or clean_text(name)
        row = db.query(VehicleBrand).filter(VehicleBrand.vehicle_type == vehicle_type, VehicleBrand.fipe_code == str(fipe_code)).first()
        if not row:
            row = VehicleBrand(vehicle_type=vehicle_type, fipe_code=str(fipe_code), canonical_name=canonical, is_active=True)
            db.add(row); db.flush()
        else:
            row.canonical_name = canonical; row.is_active = True
        self.ensure_brand_aliases(db, row, source="manual")
        return row

    def ensure_brand_aliases(self, db: Session, brand: VehicleBrand, source: str = "manual") -> None:
        aliases = set(BRAND_ALIASES.get(brand.canonical_name, [])) | {brand.canonical_name}
        existing = {a.alias for a in brand.aliases}
        pending: set[str] = set()
        with db.no_autoflush:
            for alias in aliases:
                cleaned = clean_text(alias)
                if not cleaned or cleaned in existing or cleaned in pending:
                    continue
                if not db.query(VehicleBrandAlias).filter_by(brand_id=brand.id, alias=cleaned).first():
                    db.add(VehicleBrandAlias(brand_id=brand.id, alias=cleaned, source=source))
                    pending.add(cleaned)

    def ensure_all_manual_brand_aliases(self, db: Session) -> None:
        for brand in db.query(VehicleBrand).all():
            self.ensure_brand_aliases(db, brand, source="manual")

    def ensure_model(self, db: Session, brand: VehicleBrand, fipe_code: str, name: str) -> VehicleModel:
        canonical = normalize_model_name(name) or clean_text(name)
        manual_models = MODEL_ALIASES.get(brand.canonical_name, {})
        alias_idx = model_alias_index()
        direct = alias_idx.get(clean_text(name)) or alias_idx.get(canonical)
        if direct and direct[0] == brand.canonical_name:
            canonical = direct[1]
        else:
            for known_model in manual_models:
                if clean_text(known_model) in clean_text(name):
                    canonical = known_model
                    break
        row = db.query(VehicleModel).filter(VehicleModel.brand_id == brand.id, VehicleModel.fipe_code == str(fipe_code)).first()
        if not row:
            row = VehicleModel(brand_id=brand.id, fipe_code=str(fipe_code), canonical_name=canonical, is_active=True)
            db.add(row); db.flush()
        else:
            row.canonical_name = canonical; row.is_active = True
        self.ensure_model_aliases(db, row, source="manual")
        return row

    def ensure_model_aliases(self, db: Session, model: VehicleModel, source: str = "manual") -> None:
        aliases = {model.canonical_name}
        brand_name = model.brand.canonical_name if model.brand else None
        if brand_name:
            aliases |= set(MODEL_ALIASES.get(brand_name, {}).get(model.canonical_name, []))
        existing = {a.alias for a in model.aliases}
        pending: set[str] = set()
        with db.no_autoflush:
            for alias in aliases:
                cleaned = clean_text(alias)
                normalized = normalize_model_name(alias)
                for candidate in {cleaned, normalized}:
                    if not candidate or candidate in existing or candidate in pending:
                        continue
                    if not db.query(VehicleModelAlias).filter_by(model_id=model.id, alias=candidate).first():
                        db.add(VehicleModelAlias(model_id=model.id, alias=candidate, source=source))
                        pending.add(candidate)

    def ensure_manual_alias_catalog(self, db: Session, vehicle_type: str = "carros") -> None:
        """Garante aliases brasileiros mesmo antes de uma sync FIPE completa."""
        for brand_name, models in MODEL_ALIASES.items():
            brand = db.query(VehicleBrand).filter_by(vehicle_type=vehicle_type, canonical_name=brand_name).first()
            if not brand:
                brand = VehicleBrand(vehicle_type=vehicle_type, canonical_name=brand_name, fipe_code=f"manual-{brand_name}", is_active=True)
                db.add(brand); db.flush()
            self.ensure_brand_aliases(db, brand, source="manual")
            for model_name in models.keys():
                model = db.query(VehicleModel).filter_by(brand_id=brand.id, canonical_name=model_name).first()
                if not model:
                    model = VehicleModel(brand_id=brand.id, canonical_name=model_name, fipe_code=f"manual-{brand_name}-{model_name}", is_active=True)
                    db.add(model); db.flush()
                self.ensure_model_aliases(db, model, source="manual")
        db.commit()

    def ensure_version(self, db: Session, model: VehicleModel, year_code: str, year: int, fuel: str, version_name: str, fipe_code: str, reference_month: str, fipe_price: float) -> VehicleVersion:
        row = db.query(VehicleVersion).filter_by(model_id=model.id, fipe_year_code=str(year_code), reference_month=reference_month).first()
        if not row:
            row = VehicleVersion(model_id=model.id, fipe_year_code=str(year_code), year=year, fuel=fuel, version_name=version_name, fipe_code=fipe_code, reference_month=reference_month, fipe_price=fipe_price)
            db.add(row)
        else:
            row.year = year; row.fuel = fuel; row.version_name = version_name; row.fipe_code = fipe_code; row.fipe_price = fipe_price
        return row

    def list_brands(self, db: Session, vehicle_type: str | None = None) -> list[VehicleBrand]:
        q = db.query(VehicleBrand).filter(VehicleBrand.is_active == True)
        if vehicle_type: q = q.filter(VehicleBrand.vehicle_type == vehicle_type)
        return q.order_by(VehicleBrand.canonical_name.asc()).all()

    def list_models(self, db: Session, brand_id: int) -> list[VehicleModel]:
        return db.query(VehicleModel).filter_by(brand_id=brand_id, is_active=True).order_by(VehicleModel.canonical_name.asc()).all()

    def list_versions(self, db: Session, model_id: int) -> list[VehicleVersion]:
        return db.query(VehicleVersion).filter_by(model_id=model_id).order_by(VehicleVersion.year.desc(), VehicleVersion.version_name.asc()).all()

    def search(self, db: Session, q: str, limit: int = 25) -> dict:
        term = clean_text(q)
        brands = db.query(VehicleBrand).outerjoin(VehicleBrandAlias).filter(or_(VehicleBrand.canonical_name.contains(term), VehicleBrandAlias.alias.contains(term))).limit(limit).all()
        models = db.query(VehicleModel).join(VehicleBrand).outerjoin(VehicleModelAlias).filter(or_(VehicleModel.canonical_name.contains(term), VehicleModelAlias.alias.contains(term))).limit(limit).all()
        return {"brands": brands, "models": models}

    def resolve_brand(self, db: Session, value: str) -> VehicleBrand | None:
        term = normalize_brand_name(value)
        row = db.query(VehicleBrand).outerjoin(VehicleBrandAlias).filter(or_(VehicleBrand.canonical_name == term, VehicleBrandAlias.alias == clean_text(value), VehicleBrandAlias.alias == clean_text(term))).first()
        if row: return row
        candidates = db.query(VehicleBrand).limit(500).all()
        scored = [(similarity(term, c.canonical_name), c) for c in candidates]
        scored.sort(reverse=True, key=lambda x: x[0])
        return scored[0][1] if scored and scored[0][0] >= 0.86 else None

    def resolve_model(self, db: Session, brand_id: int, value: str) -> VehicleModel | None:
        term = normalize_model_name(value)
        raw = clean_text(value)
        row = db.query(VehicleModel).outerjoin(VehicleModelAlias).filter(VehicleModel.brand_id == brand_id, or_(VehicleModel.canonical_name == term, VehicleModelAlias.alias == term, VehicleModelAlias.alias == raw)).first()
        if row: return row
        candidates = db.query(VehicleModel).filter_by(brand_id=brand_id).limit(1000).all()
        for candidate in candidates:
            aliases = [a.alias for a in candidate.aliases] + [candidate.canonical_name]
            if any(alias and (alias in raw or raw in alias or alias in term or term in alias) for alias in aliases):
                return candidate
        scored = [(max([similarity(term, c.canonical_name)] + [similarity(raw, a.alias) for a in c.aliases]), c) for c in candidates]
        scored.sort(reverse=True, key=lambda x: x[0])
        return scored[0][1] if scored and scored[0][0] >= 0.72 else None

    def normalize_vehicle_text(self, db: Session, text: str, brand_hint: str | None = None) -> CatalogMatchResult:
        raw = clean_text(" ".join([brand_hint or "", text or ""]))
        brand = self.resolve_brand(db, brand_hint or text)
        method = "fallback"
        alias = None
        if brand:
            method = "brand_alias_or_canonical"
        else:
            for token in raw.split():
                brand = self.resolve_brand(db, token)
                if brand:
                    method = "brand_token"; alias = token; break
        model = None
        if brand:
            model = self.resolve_model(db, brand.id, text)
            if model:
                method = "catalog_alias_or_fuzzy"
                for a in model.aliases:
                    if a.alias and a.alias in raw:
                        alias = a.alias; method = "exact_alias"; break
        confidence = 95 if method == "exact_alias" else 88 if model else 70 if brand else 35
        version_hint = raw
        if brand: version_hint = version_hint.replace(clean_text(brand.canonical_name), "")
        if model: version_hint = version_hint.replace(clean_text(model.canonical_name), "")
        if alias: version_hint = version_hint.replace(alias, "")
        return CatalogMatchResult(
            canonical_brand=brand.canonical_name if brand else None,
            canonical_model=model.canonical_name if model else None,
            matched_alias=alias,
            confidence_score=confidence,
            match_method=method,
            version_hint=" ".join(version_hint.split()) or None,
        )
