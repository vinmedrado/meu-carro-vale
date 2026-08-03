# Meu Carro Vale

**Meu Carro Vale** é uma plataforma SaaS de valuation automotivo inteligente para o mercado brasileiro. O produto combina FIPE local-first, dados reais de mercado, comparáveis de anúncios, dashboard premium, laudo PDF e gates de monetização para ajudar usuários a estimar o valor correto de venda de carros com mais clareza e confiança.

> Status: projeto disponível para demonstração local, portfólio técnico e preparação de deploy. Integrações de pagamento permanecem em modo **Pagar.me-ready**, sem cobrança real por padrão.

---

## Visão geral

A plataforma orienta o usuário por um wizard de avaliação, calcula uma faixa de preço com base em dados disponíveis, exibe um dashboard visual com score, comparáveis e insights, e permite exportar um laudo premium conforme o plano contratado.

O foco do projeto é demonstrar uma arquitetura SaaS completa, com backend em FastAPI, frontend React premium, PostgreSQL, Alembic, Docker Compose, tracking de uso e preparação para billing.

---

## Problema resolvido

Vender um veículo pelo preço errado pode gerar perda financeira, baixa liquidez ou demora excessiva na negociação. A FIPE sozinha nem sempre reflete anúncios ativos, diferenças regionais, quilometragem, estado do veículo e estratégia de venda.

O Meu Carro Vale centraliza esses sinais em uma experiência simples:

- coleta informações do veículo;
- consulta dados locais de referência;
- usa comparáveis reais quando disponíveis;
- explica a fonte e a confiança do cálculo;
- gera um relatório profissional para apoiar a venda.

---

## Diferenciais do produto

- **FIPE local-first:** evita quebrar o fluxo do usuário quando APIs externas ficam indisponíveis ou rate limited.
- **Dados reais de mercado:** estrutura preparada para Mercado Livre API e registros locais de anúncios.
- **Transparência:** o dashboard mostra fonte dos dados, confiança e avisos quando houver fallback.
- **UX premium:** wizard, dashboard, admin e PDF com linguagem visual de SaaS financeiro.
- **Monetização:** planos FREE, PRO e BUSINESS com gates de uso, PDF e comparáveis.
- **Deploy-ready:** Docker Compose, Alembic, seed demo e documentação operacional.

---

## Funcionalidades principais

- Wizard premium de avaliação do veículo.
- Valuation com faixa de venda rápida, preço ideal e valor premium.
- Result Dashboard Premium com score, comparáveis, distribuição e insights.
- Exportação de laudo PDF premium.
- Admin Dashboard para saúde dos dados e operações.
- FIPE cache/local-first com fallback seguro.
- Adapter Mercado Livre API para dados de mercado.
- Tracking de uso mensal por tenant/usuário.
- Gates de planos e preparação para Pagar.me.

---

## Stack técnica

### Backend

- FastAPI
- SQLAlchemy
- Alembic
- PostgreSQL
- Passlib para hash de senha
- Pytest

### Frontend

- React
- Vite
- TypeScript
- Tailwind CSS
- Framer Motion
- Recharts
- jsPDF/html2canvas para PDF

### Infra local

- Docker Compose
- PostgreSQL 16
- Redis 7

---

## Arquitetura

```text
Usuário
  ↓
Frontend React/Vite
  ↓
Backend FastAPI
  ├─ Auth/JWT
  ├─ Valuation Engine
  ├─ FIPE Service local-first
  ├─ Market Data Services
  ├─ SaaS/Billing Gates
  └─ Admin/Data Operations
  ↓
PostgreSQL + Alembic
```

O `mcv-data-engine/` permanece como módulo separado para coleta/processamento de dados, enquanto o backend principal consome dados persistidos e expõe endpoints para a experiência SaaS.

---

## Fluxo do produto

1. Usuário acessa a landing/app.
2. Preenche o Wizard de Avaliação.
3. Backend valida gates de uso do plano.
4. Valuation consulta FIPE local e dados de mercado disponíveis.
5. Result Dashboard exibe score, faixa de preço, comparáveis e insights.
6. Usuário PRO/BUSINESS pode exportar PDF.
7. Admin acompanha saúde de FIPE, market data e jobs.

---

## Fluxo de dados

```text
FIPE/API externa → Cache local PostgreSQL → Valuation
Mercado Livre API → market_listings → Comparáveis/estatísticas → Valuation
Valuation → valuation_reports → Dashboard/PDF/Histórico
UsageTracking → Gates de plano → Controle de monetização
```

Quando dados reais são insuficientes, o sistema mantém fallback explícito e honesto na interface.

---

## Como rodar localmente

### 1. Preparar variáveis

```bash
cp .env.example .env
```

Revise `.env` antes de subir os containers. Para demo local, mantenha:

```env
PAGARME_ENABLED=false
APP_ENV=local
DEMO_MODE=true
```

### 2. Subir containers

```bash
docker compose up -d
```

### 3. Rodar migrations

```bash
docker compose exec backend alembic -c /workspace/alembic.ini upgrade head
```

### 4. Rodar seed demo

```bash
docker compose exec backend python /app/scripts/seed_demo.py
```

### 5. Acessar

- Frontend: `http://localhost:9000`
- Backend: `http://localhost:8020`
- Docs FastAPI: `http://localhost:8020/docs`

---

## Variáveis de ambiente

Principais variáveis usadas localmente:

| Variável | Uso |
|---|---|
| `DATABASE_URL` | conexão SQLAlchemy com PostgreSQL |
| `JWT_SECRET` | assinatura dos tokens JWT |
| `FRONTEND_URL` | origem principal do frontend |
| `BACKEND_CORS_ORIGINS` | origens liberadas no CORS |
| `PAGARME_ENABLED` | liga/desliga billing real |
| `PAGARME_API_KEY` | chave Pagar.me quando habilitado |
| `PAGARME_WEBHOOK_SECRET` | validação de webhook Pagar.me |
| `VITE_API_URL` | URL do backend para o frontend |
| `FIPE_CACHE_TTL_SECONDS` | TTL do cache FIPE |
| `MARKET_COLLECTION_ENABLED` | habilita coleta de mercado |
| `MCV_DATA_ENGINE_API_URL` | URL opcional do data engine |

> Use `JWT_SECRET`, não `SECRET_KEY`. A documentação foi padronizada conforme o backend.

---

## Seed demo

O seed local cria dados mínimos e idempotentes para demonstração:

- tenant demo;
- usuário demo;
- planos FREE/PRO/BUSINESS;
- assinatura FREE local;
- usage tracking zerado;
- FIPE demo;
- market listings demo;
- valuation report demo.

Executar:

```bash
docker compose exec backend python /app/scripts/seed_demo.py
```

O seed usa a função real de hash do projeto (`app.core.security.hash_password`) e não cria pagamento real.

---

## Login demo

```text
Email: demo@meucarrovale.local
Senha: Demo@123456
```

---

## Testes

Backend:

```bash
docker compose exec backend pytest
```

Compilação pontual de arquivos Python:

```bash
python -m py_compile backend/scripts/seed_demo.py
```

Frontend:

```bash
cd frontend
npm ci
npm run build
```

---

## Build frontend

Para validar o build de produção:

```bash
cd frontend
npm ci
npm run build
```

O output fica em `frontend/dist/`.

---

## Docker

Comandos úteis:

```bash
docker compose config
docker compose up -d
docker compose logs -f backend
docker compose logs -f frontend
docker compose down
```

O backend monta o código em `/app` e as migrations Alembic em `/workspace`, por isso o comando de migration usa:

```bash
docker compose exec backend alembic -c /workspace/alembic.ini upgrade head
```

---

## Alembic/migrations

Rodar migrations:

```bash
docker compose exec backend alembic -c /workspace/alembic.ini upgrade head
```

Criar nova migration, se necessário:

```bash
docker compose exec backend alembic -c /workspace/alembic.ini revision -m "descricao_da_migration"
```

---

## Pagar.me-ready

O projeto está preparado para billing com Pagar.me, mas o modo local deve permanecer desativado:

```env
PAGARME_ENABLED=false
```

Em produção, configure chaves reais somente no ambiente seguro do provedor de deploy. Não versionar segredos.

---

## APIs externas

- FIPE/Parallelum: usada como fonte externa quando disponível, com cache local-first.
- Mercado Livre API: usada para coleta pública de anúncios quando habilitada.

A aplicação deve continuar funcionando em modo degradado se APIs externas falharem.

---

## Screenshots

Sugestão de capturas para documentação visual após rodar o projeto localmente:

```text
docs/screenshots/landing.png
docs/screenshots/wizard.png
docs/screenshots/result-dashboard.png
docs/screenshots/admin-dashboard.png
docs/screenshots/pdf-report.png
```

---

## Roadmap

- Deploy de backend e frontend em ambiente cloud.
- Monitoramento de jobs e logs em produção.
- Webhooks Pagar.me em ambiente real.
- Expansão controlada de market data.
- Treinamento futuro de modelos ML quando houver volume suficiente.

---

## Troubleshooting

### `alembic.ini` não encontrado

Use o comando completo:

```bash
docker compose exec backend alembic -c /workspace/alembic.ini upgrade head
```

### Login demo não funciona

Reexecute o seed após migrations:

```bash
docker compose exec backend python /app/scripts/seed_demo.py
```

### Frontend não encontra backend

Confira `VITE_API_URL` e se o backend está em `http://localhost:8020`.

### CORS bloqueando requisições

Verifique `BACKEND_CORS_ORIGINS` no `.env`.

### Billing aparece indisponível

Para demo local, isso é esperado com `PAGARME_ENABLED=false`.

---

## Status do projeto

Projeto em estágio **portfolio/demo-ready**, com arquitetura SaaS funcional e preparação para deploy. Antes de produção real, revisar secrets, domínio, HTTPS, webhooks Pagar.me, backups e observabilidade.

## Licença

MIT.
