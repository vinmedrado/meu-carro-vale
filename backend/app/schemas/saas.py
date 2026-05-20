from __future__ import annotations
from pydantic import BaseModel, EmailStr

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    tenant_name: str | None = None
    tenant_type: str = "usuario_individual"

class RefreshRequest(BaseModel):
    refresh_token: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class CheckoutRequest(BaseModel):
    plan_id: str
    provider: str = "mercado_pago"
