# Meu Carro Vale

Plataforma de valuation automotivo inteligente para vender veiculos com mais confianca, transparencia e poder de negociacao.

## Visao geral

O projeto transforma dados do veiculo em leitura comercial: faixa recomendada, indice de liquidez, comparacao com FIPE, potencial perdido e laudo executivo exportavel.

## Problema que resolve

- Vendedores que anunciam abaixo do mercado.
- Compradores com mais referencia de preco do que o vendedor.
- FIPE isolada sem contexto de mercado.
- Dificuldade para justificar o valor pedido.

## Arquitetura

```text
frontend/            UI React
backend/             API FastAPI
mcv-data-engine/     contratos e exportacoes oficiais
docs/                documentacao tecnica
screenshots/         capturas do produto
```

## Screenshots

![Portfolio screenshot](https://raw.githubusercontent.com/vinmedrado/portfolio/main/images/meucarrovale.png)

## Funcionalidades

- Modo DEMO para showcase.
- Modo REAL com FIPE e dados de mercado.
- Catalogo mestre automotivo.
- Sincronizacao FIPE em background.
- Liquidez e comparaveis.
- Laudo em PDF.
- Geracao de anuncio.
- Camada SaaS e historico de laudos.

## Tecnologias

Python, FastAPI, React, TypeScript, Vite, SQLAlchemy, PostgreSQL, Docker, Alembic.

## Como executar

### Docker

```bash
cp .env.example .env
docker compose up --build
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Backend

```bash
cd backend
pip install -r requirements.txt
python -m app.db.init_db
uvicorn app.main:app --reload --host 127.0.0.1 --port 8010
```

## Estrutura do projeto

```text
backend/          API e dominio
frontend/         app principal
mcv-data-engine/  contratos de dados
docs/             arquitetura e operacao
screenshots/      capturas do produto
```

## Roadmap

- Consolidar evidencias visuais reais no README.
- Continuar a integracao com o mcv-data-engine.
- Refinar a narrativa comercial do laudo.

## Licenca

TODO.
