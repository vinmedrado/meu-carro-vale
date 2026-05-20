from __future__ import annotations
from dataclasses import dataclass

@dataclass
class CheckoutSession:
    provider: str
    status: str
    message: str
    checkout_url: str | None = None

class BillingProvider:
    provider_name = "manual"
    def create_checkout_session(self, tenant_id: str, plan_id: str) -> CheckoutSession:
        return CheckoutSession(self.provider_name, "preparado", "Cobrança preparada. Configure credenciais para checkout real.")
    def handle_webhook(self, payload: dict) -> dict:
        return {"status": "recebido", "provider": self.provider_name, "payload_keys": list(payload.keys())}

class MercadoPagoProvider(BillingProvider):
    provider_name = "mercado_pago"

class StripeProvider(BillingProvider):
    provider_name = "stripe"

def get_provider(name: str) -> BillingProvider:
    return StripeProvider() if name == "stripe" else MercadoPagoProvider()
