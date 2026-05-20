from __future__ import annotations

from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from app.api.deps import current_user
from app.core.config import settings
from app.core.security import create_refresh_token, create_token, hash_password, verify_password
from app.db.session import get_db
from app.models.saas import RefreshToken
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.saas import ForgotPasswordRequest, RefreshRequest, RegisterRequest
from app.services.saas_service import create_tenant_for_user, ensure_demo_tenant, token_digest

router = APIRouter(prefix="/auth", tags=["auth"])


def _store_refresh_token(db: Session, user: User, refresh_token: str) -> None:
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    db.add(RefreshToken(tenant_id=user.tenant_id, user_id=user.id, token_hash=token_digest(refresh_token), expires_at=expires_at))
    db.commit()


def token_payload(db: Session, user: User):
    access = create_token(user.email, settings.access_token_expire_minutes)
    refresh = create_refresh_token(user.email)
    _store_refresh_token(db, user, refresh)
    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        user={"id": user.id, "name": user.name, "email": user.email, "tenant_id": user.tenant_id, "role": getattr(user, "role", "owner")},
    )


@router.post("/register", response_model=TokenResponse)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=409, detail="E-mail já cadastrado")
    if len(data.password) < 8:
        raise HTTPException(status_code=422, detail="A senha deve ter pelo menos 8 caracteres")
    user = User(name=data.name, email=data.email, password_hash=hash_password(data.password), tenant_id="pending", role="owner")
    db.add(user)
    db.commit()
    db.refresh(user)
    create_tenant_for_user(db, user, getattr(data, "tenant_name", None), getattr(data, "tenant_type", "usuario_individual"))
    return token_payload(db, user)


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    return token_payload(db, user)


@router.post("/refresh", response_model=TokenResponse)
def refresh(data: RefreshRequest, db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(data.refresh_token, settings.jwt_secret, algorithms=["HS256"])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Token de atualização inválido")
        email = payload.get("sub")
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="Token de atualização inválido") from exc
    user = db.query(User).filter(User.email == email).first()
    stored = db.query(RefreshToken).filter(RefreshToken.token_hash == token_digest(data.refresh_token), RefreshToken.revoked == False).first()  # noqa: E712
    if not user or not stored:
        raise HTTPException(status_code=401, detail="Sessão expirada")
    stored.revoked = True
    db.commit()
    return token_payload(db, user)


@router.post("/logout")
def logout(data: RefreshRequest | None = None, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if data and data.refresh_token:
        stored = db.query(RefreshToken).filter(RefreshToken.token_hash == token_digest(data.refresh_token)).first()
        if stored and stored.tenant_id == user.tenant_id:
            stored.revoked = True
            db.commit()
    return {"message": "Sessão encerrada"}


@router.post("/forgot-password")
def forgot_password(data: ForgotPasswordRequest):
    return {"message": "Recuperação de senha preparada. Configure um provedor de e-mail para envio real.", "email": data.email}


@router.get("/me")
def me(user: User = Depends(current_user)):
    return {"id": user.id, "name": user.name, "email": user.email, "tenant_id": user.tenant_id, "role": getattr(user, "role", "owner")}


@router.post("/demo", response_model=TokenResponse)
def demo(db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == "demo@meucarrovale.com.br").first()
    if not user:
        user = User(name="Demonstração", email="demo@meucarrovale.com.br", password_hash=hash_password("demo12345"), tenant_id="demo-tenant", role="owner")
        db.add(user); db.commit(); db.refresh(user)
    ensure_demo_tenant(db, user)
    return token_payload(db, user)
