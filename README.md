<p align="center">
  </p>

# Meu Carro Vale

<p align="center">
  <strong>Valuation automotivo inteligente para vender veículos com mais confiança, transparência e poder de negociação.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/status-MVP%20real%20engine-111827?style=for-the-badge" />
  <img src="https://img.shields.io/badge/frontend-React%20%2B%20Vite-111827?style=for-the-badge" />
  <img src="https://img.shields.io/badge/backend-FastAPI-111827?style=for-the-badge" />
  <img src="https://img.shields.io/badge/docker-ready-111827?style=for-the-badge" />
</p>

## Visão geral

O **Meu Carro Vale** é uma plataforma brasileira de inteligência automotiva criada para ajudar pessoas a venderem carros pelo valor correto. O produto transforma dados do veículo em uma análise visual de mercado, com faixa recomendada, índice de liquidez, comparação com FIPE real no modo REAL, catálogo mestre, potencial financeiro perdido e laudo executivo exportável.

A proposta não é apenas “calcular preço”. É entregar uma experiência de negociação: o usuário entende o valor do veículo, visualiza argumentos comerciais e sai com um relatório profissional para defender sua proposta.

## Problema

Vender um veículo no Brasil ainda é um processo pouco transparente. Muitas pessoas anunciam abaixo do mercado, aceitam propostas agressivas ou não sabem justificar o preço pedido.

O resultado é uma negociação desigual:

- o comprador costuma chegar com mais referência de preço;
- o vendedor não sabe medir liquidez, praça e condição;
- a FIPE isolada não explica o valor real de negociação;
- bons veículos podem perder valor por falta de apresentação e argumento.

## Solução

O Meu Carro Vale oferece uma camada de inteligência para apoiar a decisão de venda.

A plataforma combina valuation, análise de mercado, leitura de liquidez, comparação com referência FIPE, potencial perdido e geração de anúncio em uma interface sofisticada, simples e orientada à negociação.

## Funcionalidades principais

- **Índice Meu Carro Vale™**: nota visual que resume força comercial, liquidez e atratividade do veículo.
- **Valor de Mercado™**: leitura de faixa segura, venda rápida, mercado atual e teto sofisticado.
- **Potencial Perdido™**: diferença estimada entre proposta conservadora e valor recomendado.
- **Laudo em PDF**: exportação real do relatório para apresentação e negociação.
- **Geração de anúncio**: título, descrição, versão curta e destaques comerciais.
- **Upload de imagens**: preview de fotos e base para avaliação visual.
- **Comparação com FIPE**: referência real no `APP_MODE=REAL`, com cache/tabelas locais; no `APP_MODE=DEMO`, usa dados reduzidos apenas para showcase.
- **Liquidez**: leitura de facilidade de venda e força regional.
- **Relatório executivo**: experiência visual pensada para demonstração pública e validação real.

## Modos de operação

### APP_MODE=DEMO

Modo separado para apresentação rápida, vídeo, GitHub e validação visual. Pode usar catálogo reduzido e dados demonstrativos sem travar a experiência.

### APP_MODE=REAL

Modo de inteligência real. O cálculo principal usa catálogo mestre FIPE, cache FIPE, comparáveis reais/importados, estatísticas de mercado, liquidez e engine real. Não deve depender de CSV manual ou número fixo como fonte principal.

## Catálogo mestre automotivo

O projeto possui uma camada `backend/app/vehicle_catalog/` para manter marcas, modelos, versões, códigos FIPE e aliases normalizados. A base inicial vem da FIPE real por tipo de veículo:

- carros;
- motos;
- caminhões.

Tabelas principais:

- `vehicle_brands`;
- `vehicle_brand_aliases`;
- `vehicle_models`;
- `vehicle_model_aliases`;
- `vehicle_versions`;
- `vehicle_catalog_sync_jobs`.

O catálogo sincroniza marcas, modelos, anos/versões, código FIPE, combustível, mês de referência e preço FIPE. Registros existentes são atualizados e duplicidades são evitadas por constraints e lógica de upsert.

## Sincronização FIPE em background

A rota `POST /api/catalog/sync-fipe` inicia uma sincronização assíncrona e retorna um `job_id`, sem travar a API.

Rotas disponíveis:

- `GET /api/catalog/brands`;
- `GET /api/catalog/models?brand_id=`;
- `GET /api/catalog/versions?model_id=`;
- `GET /api/catalog/search?q=`;
- `GET /api/catalog/normalize?q=`;
- `POST /api/catalog/sync-fipe?vehicle_type=carros`;
- `POST /api/catalog/sync-fipe?vehicle_type=motos`;
- `POST /api/catalog/sync-fipe?vehicle_type=caminhoes`;
- `GET /api/catalog/sync-status/{job_id}`;
- `GET /api/catalog/sync-jobs`;
- `GET /api/catalog/admin/overview`.

Status de job:

- `pending`;
- `running`;
- `completed`;
- `failed`;
- `partial_success`.

O painel interno mostra total de marcas, modelos, versões, última sincronização, progresso percentual e erros recentes.

## Aliases e normalização

O catálogo inclui aliases brasileiros para marcas e modelos. Exemplos:

- `GM`, `General Motors`, `Chevy` → Chevrolet;
- `VW`, `Volks`, `Wolkswagen` → Volkswagen;
- `Prisma` → Chevrolet Onix Plus;
- `Corsa Classic` → Chevrolet Corsa;
- `TCross` → Volkswagen T-Cross;
- `HRV` → Honda HR-V;
- `S-10` → Chevrolet S10;
- `Hilux SW4` → Toyota SW4.

A normalização segue a ordem:

1. match exato por alias;
2. match canônico;
3. fuzzy matching;
4. fallback para texto normalizado.

O retorno técnico inclui `canonical_brand`, `canonical_model`, `matched_alias`, `confidence_score`, `match_method` e `version_hint`. Antes do valuation real buscar comparáveis, marca/modelo são normalizados pelo catálogo para melhorar a precisão.

## Experiência demo

O projeto inclui um modo de demonstração pronto para showcase.

Fluxo recomendado:

1. Abrir a landing editorial.
2. Clicar em **Avaliar meu veículo** ou **Ver demonstração**.
3. Entrar no painel com veículo pré-carregado.
4. Revisar o laudo sofisticado.
5. Visualizar Potencial Perdido™.
6. Exportar PDF.
7. Gerar anúncio comercial.

### Veículos demo incluídos

- Toyota Corolla XEi 2021
- BMW 320i Sport GP 2020
- Honda Civic Touring 2019
- Jeep Compass Limited 2022

Os dados demo foram preparados para abrir o produto rapidamente em vídeo, entrevista, GitHub ou validação com usuários.

## Screenshots

### Landing editorial


### Painel de negociação


### Laudo na interface


### Experiência mobile


### PDF exportável


## Stack

### Frontend

- React
- Vite
- TypeScript
- Tailwind CSS
- Framer Motion
- Recharts
- Lucide React
- jsPDF

### Backend

- FastAPI
- SQLAlchemy
- PostgreSQL
- JWT
- Docker

## Como rodar com Docker

```bash
cp .env.example .env
docker compose up --build
```

Acesse:

```text
Frontend: http://localhost:5180
Backend:  http://localhost:8010/docs
```

## Como rodar o frontend localmente

```bash
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5180
```

## Como rodar o backend localmente

```bash
cd backend
pip install -r requirements.txt
python -m app.db.init_db
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8010
```

## Build de produção

```bash
cd frontend
npm run build
```

## Estrutura do projeto

```text
meu_carro_vale/
  backend/
    app/
      api/
      core/
      db/
      models/
      schemas/
      services/
    Dockerfile
    requirements.txt
  frontend/
    src/
      app/
      components/
      data/
      features/
      hooks/
      lib/
      styles/
      types/
    Dockerfile
    package.json
  screenshots/
    landing/
    dashboard/
    report/
    mobile/
    pdf/
  docs/
  docker-compose.yml
  README.md
```

## Status do MVP

**MVP funcional com modo DEMO separado e modo REAL para cálculo baseado em dados reais.**

O projeto está preparado para:

- apresentação pública no GitHub;
- gravação de vídeo demo;
- validação inicial com usuários;
- conversa com recrutadores, clientes e potenciais parceiros;
- evolução futura para fontes reais de mercado.

Importante: o modo DEMO é separado e usa dados demonstrativos apenas para showcase. Em APP_MODE=REAL, o cálculo principal exige FIPE real/cache real e/ou dados de mercado coletados/importados, sem inventar valuation quando não houver base suficiente.

## Roadmap

- Integração real com FIPE e bases públicas/privadas de anúncios.
- Histórico de preço por região, versão e quilometragem.
- Conta do usuário com múltiplos veículos salvos.
- Link público compartilhável do laudo.
- Comparação com anúncios semelhantes reais.
- Camada de visão computacional para qualidade das fotos.
- Planos para vendedores, lojistas, consultores e despachantes.

## Posicionamento

Meu Carro Vale foi pensado como uma startup brasileira de alto padrão para trazer mais inteligência, clareza e poder de negociação ao mercado automotivo.


---

## Modo DEMO x Modo REAL

O Meu Carro Vale agora possui separação explícita de modo de execução.

### `APP_MODE=DEMO`
Usado para apresentação, vídeo demo, GitHub e showcase rápido. Mantém veículos pré-preenchidos e dados demonstrativos com selo **Modo demonstração**.

### `APP_MODE=REAL`
Usado para cálculo real. Neste modo o backend não usa mock como valor principal. O cálculo exige pelo menos uma destas bases:

- FIPE real consultada e salva em cache local;
- anúncios reais importados por CSV no banco `market_listings`.

Se o modo real não encontrar FIPE/cache nem anúncios comparáveis, a API retorna erro controlado em vez de inventar preço.

## Fontes de dados reais

### FIPE real
Rotas disponíveis:

```bash
GET /api/fipe/brands?vehicle_type=carros
GET /api/fipe/models?vehicle_type=carros&brand_code=59
GET /api/fipe/years?vehicle_type=carros&brand_code=59&model_code=5940
GET /api/fipe/price?vehicle_type=carros&brand_code=59&model_code=5940&year_code=2021-1
```

A resposta normalizada salva:

- tipo do veículo;
- marca;
- modelo;
- ano;
- código FIPE;
- combustível;
- mês de referência;
- valor FIPE.

### Anúncios reais
A arquitetura de fontes é plugável em `backend/app/market_sources/`.

Adaptadores preparados:

- OLX;
- Webmotors;
- iCarros;
- Mercado Livre;
- CSV.

Por segurança jurídica e operacional, os adaptadores de scraping direto ficam desabilitados inicialmente. O caminho imediato recomendado é API/parceria/importação CSV, respeitando robots.txt, limites de acesso e termos das plataformas.

## Importação CSV real

Endpoint:

```bash
POST /api/market/import-csv
```

Colunas aceitas:

```csv
title,price,brand,model,version,year,mileage,city,state,transmission,fuel,url,source
```

Existe um exemplo em:

```bash
docs/data/anuncios_reais_exemplo.csv
```

Exemplo com `curl`:

```bash
curl -X POST http://localhost:8000/api/market/import-csv \
  -H "Authorization: Bearer SEU_TOKEN" \
  -F "file=@docs/data/anuncios_reais_exemplo.csv"
```

## Metodologia do cálculo real

O `valuation_real_engine.py` calcula preço usando:

- seleção de comparáveis por marca, modelo, ano, estado, versão, câmbio, combustível e km;
- `similarity_score` de 0 a 100;
- corte mínimo configurável por `MIN_COMPARABLE_SCORE`;
- mediana, P25, P50 e P75;
- remoção de outliers por IQR;
- ajuste por quilometragem acima/abaixo da mediana;
- ajuste por conservação;
- ajuste regional;
- FIPE real como âncora secundária;
- score de confiança por quantidade, qualidade, recência, dispersão e presença de FIPE.

Saídas principais:

- venda rápida;
- valor justo;
- valor valorizado;
- faixa de negociação;
- potencial perdido;
- liquidez;
- índice Meu Carro Vale;
- confiança do cálculo;
- comparáveis usados.

## Banco de dados real

Novas tabelas:

- `fipe_prices`;
- `market_listings`;
- `valuation_runs`;
- `valuation_comparables`.

Migration Alembic:

```bash
alembic upgrade head
```

O app também chama a inicialização no startup local. Para forçar a criação das tabelas e do catálogo mínimo manualmente:

```bash
cd backend
python -m app.db.init_db
```

## Rodar em modo real

No `.env`:

```env
APP_MODE=REAL
MIN_COMPARABLE_SCORE=62
FIPE_CACHE_TTL_SECONDS=43200
```

Fluxo recomendado:

1. Subir backend e frontend.
2. Consultar/salvar FIPE real pela rota `/api/fipe/price`.
3. Importar CSV real de anúncios em `/api/market/import-csv`.
4. Gerar valuation normalmente pelo frontend.
5. Conferir no laudo: **Análise com dados reais**, FIPE, quantidade de comparáveis, confiança e metodologia.

## Limitações atuais

- Scraping direto de marketplaces permanece desabilitado por padrão para respeitar termos, robots.txt e limites de acesso.
- A qualidade do modo real depende da base de anúncios importada e da existência de FIPE/cache.
- Regiões com poucos anúncios podem gerar confiança baixa; nesses casos o laudo mostra aviso metodológico conservador.

## Market Intelligence Automotiva Real

Este patch transforma o Meu Carro Vale de um valuation app para uma plataforma de inteligência de mercado automotivo, preservando o frontend refinado e o modo demonstração.

### Estrutura criada

A camada principal fica em `backend/app/market_intelligence/`:

- `collectors/`: arquitetura plugável para OLX, Webmotors, iCarros e Mercado Livre, com coletores desabilitados por padrão até validação de API/ToS/robots.
- `pipelines/`: ingestão responsável, normalização, deduplicação e histórico.
- `normalizers/`: aliases, limpeza textual, marca/modelo/versão, combustível, câmbio, cidade/UF, km e preço.
- `deduplication/`: fingerprint e `duplicate_score` para repostagens, clones e anúncios reciclados.
- `comparables/`: engine de comparáveis com `similarity_score` 0–100.
- `valuation/`: `valuation_engine_v3.py`, com FIPE real/cache, mediana ponderada, percentis, média aparada, remoção de outliers, ajuste regional, km, liquidez e qualidade da amostra.
- `liquidity/`: score e classificação `Muito Alta`, `Alta`, `Média` e `Baixa`.
- `analytics/`: filtros IQR, z-score e suspeita de preço/km/ano impossível.
- `jobs/` e `schedulers/`: jobs para estatísticas, snapshots, liquidez e filas de coleta.
- `cache/`: cache TTL local preparado para evolução com Redis.
- `storage/`: reservado para persistência e contratos de armazenamento.

### APP_MODE

`APP_MODE=DEMO` mantém showcase e mock permitido.

`APP_MODE=REAL` exige dados reais. O cálculo principal real não usa mock: precisa de FIPE em cache via serviço FIPE e/ou anúncios reais coletados/importados. Se não houver base real suficiente, a API retorna erro controlado em vez de inventar valuation.

### Banco expandido

Migração `0003_market_intelligence_infrastructure.py` adiciona:

- `market_listing_history`
- `market_snapshots`
- `market_price_stats`
- `market_liquidity`
- `market_collection_jobs`
- campos de deduplicação em `market_listings`: `seller_type`, `fingerprint`, `duplicate_score`, `is_active`

### Coleta responsável

Os coletores externos foram criados em modo plugável e seguro. Eles respeitam rate limiting, retries, backoff e checagem de `robots.txt`. Por padrão, ficam desabilitados até existir permissão clara por API, parceria, ToS ou fonte pública compatível.

### Endpoints administrativos

- `GET /api/market/admin/overview`: visão interna de anúncios, fontes, regiões, duplicados, jobs e snapshots.
- `POST /api/market/admin/rebuild-statistics`: recalcula estatísticas, liquidez e snapshot.
- `POST /api/market/admin/jobs?source=...`: cria job de coleta controlado.

### Metodologia do Valuation v3

O valuation real combina:

- FIPE real/cache como âncora secundária.
- Comparáveis reais ponderados por similaridade.
- Mediana ponderada, P25/P50/P75 e média aparada.
- Remoção de outliers por IQR/z-score.
- Ajuste por km, conservação, região, recência, liquidez e qualidade da amostra.
- `confidence_score` baseado em quantidade de comparáveis, dispersão, similaridade, FIPE, cobertura regional e liquidez.

### Testes adicionados

Cobertura inicial em `backend/tests/test_market_intelligence.py`:

- normalização;
- outliers;
- deduplicação;
- liquidez.

Comando:

```bash
PYTHONPATH=backend pytest -q backend/tests
```

## Catálogo Mestre Automotivo

O Meu Carro Vale agora possui uma camada incremental de catálogo mestre em `backend/app/vehicle_catalog`, usando a FIPE como base inicial para normalizar marcas, modelos, anos, versões, códigos FIPE e tipos de veículo (`carros`, `motos` e `caminhoes`).

### Sincronização FIPE

O job `backend/app/vehicle_catalog/jobs/sync_vehicle_catalog_from_fipe.py` executa o fluxo real:

1. busca marcas por tipo de veículo;
2. busca modelos por marca;
3. busca anos por modelo;
4. busca preço/versão FIPE;
5. salva marcas, modelos, versões e aliases no banco;
6. evita duplicidade por chaves únicas de FIPE;
7. atualiza registros existentes;
8. registra logs em `vehicle_catalog_sync_logs`.

Rotas disponíveis:

- `GET /api/catalog/brands?vehicle_type=carros`
- `GET /api/catalog/models?brand_id=`
- `GET /api/catalog/versions?model_id=`
- `GET /api/catalog/search?q=`
- `POST /api/catalog/sync-fipe`
- `GET /api/catalog/admin/overview`

### Aliases e normalização

Aliases iniciais cobrem marcas importantes do Brasil, como Chevrolet/GM/General Motors/Chevy, Volkswagen/VW/Volks/Wolks, Mercedes-Benz/Mercedes/MB, Fiat/FCA Fiat, Toyota/Toyta, Honda/Hoda e Land Rover/Range Rover. A avaliação e a normalização de anúncios passam a tentar resolver marca/modelo pelo catálogo antes de usar texto livre.

### Uso no valuation real

Em `APP_MODE=REAL`, o valuation continua proibido de usar mock no cálculo principal. Quando existir catálogo FIPE sincronizado, a engine v3 também pode usar `vehicle_versions` como fonte FIPE estruturada, além do cache `fipe_prices` e dos comparáveis reais.

### APP_MODE

- `APP_MODE=DEMO`: catálogo reduzido pode ser sincronizado com limites para showcase.
- `APP_MODE=REAL`: a base esperada é catálogo FIPE sincronizado e dados reais de mercado.

### Limitações responsáveis

A sincronização depende de disponibilidade da API pública FIPE/Parallelum e deve respeitar limites de execução. Para produção, recomenda-se agendar em janelas controladas, manter cache e monitorar `vehicle_catalog_sync_logs`.

## Valuation transparente

O Meu Carro Vale agora apresenta o valuation como um laudo explicável, não apenas como um número final.

O cálculo expõe:

- comparáveis usados no cálculo;
- quantidade de anúncios semelhantes;
- escopo regional utilizado;
- faixa de ano e quilometragem considerada;
- dispersão de preços com mínimo, P25, P50/mediana, P75 e máximo;
- score de confiança com explicação humana;
- liquidez real com leitura de procura e oferta;
- pesos de FIPE e mercado real;
- outliers removidos;
- metodologia simplificada para o usuário entender a origem do valor.

Em modo real, o valuation mantém a arquitetura de market intelligence, catálogo FIPE e comparáveis reais. A FIPE funciona como referência secundária, enquanto o mercado real é o principal indicador quando há amostra suficiente. O PDF exportável também inclui metodologia, comparáveis, confiança, liquidez, snapshot de mercado e dispersão.

## MCV Intelligence Engine

A plataforma agora possui uma camada dedicada de inteligência automotiva em `backend/app/intelligence/`, preservando a valuation engine existente e adicionando explicabilidade operacional para transformar o Meu Carro Vale em uma plataforma de inteligência de mercado.

Camadas adicionadas:

- **Market Live Data Engine**: contratos de provedores, normalização, fingerprints, deduplicação e snapshots para OLX, Webmotors, iCarros, Kavak, FIPE e fontes autorizadas.
- **Comparable Engine**: ranking de comparáveis por modelo, versão, ano, km, região, combustível, transmissão e distância de mercado.
- **Liquidity Engine**: leitura de volume, demanda, saturação, temperatura de mercado e velocidade esperada de venda.
- **Negotiation Engine**: calcula venda rápida, valor indicado, piso, teto e margem estimada de negociação.
- **Confidence Engine**: mede qualidade do valuation por quantidade de comparáveis, dispersão, FIPE, região e liquidez.
- **Regional Engine**: aplica multiplicador regional e leitura de praça para diferenças entre estados/capitais/interior.
- **Market Trend Engine**: prepara tendência semanal/mensal, dispersão e sazonalidade para evolução com histórico.

Novas estruturas importantes:

```text
backend/app/intelligence/
  providers/
  normalization/
  comparables/
  liquidity/
  negotiation/
  confidence/
  regional/
  trends/

backend/app/ml/
  datasets/
  features/
  models/
  training/
  inference/
```

Novas tabelas preparadas via Alembic e `Base.metadata.create_all` local:

- `comparable_vehicles`
- `valuation_confidence`
- `market_liquidity`
- `negotiation_ranges`
- `regional_valuation`
- `market_trends`
- `market_snapshots`

Endpoint de visão geral:

```text
GET /api/intelligence/overview
```

O backend não habilita scraping agressivo por padrão. As fontes externas devem usar APIs, CSVs autorizados, parcerias ou rotinas permitidas pelos termos de cada origem.

## MCV Explainable Valuation Engine

Esta versão adiciona uma camada consultiva sobre a MCV Intelligence Engine sem substituir a valuation engine existente. O retorno de valuation passa a explicar a faixa recomendada com base nos fatores disponíveis:

- `valuation_explanation`: impactos positivos e negativos por fator, com peso e motivo.
- `comparable_analysis`: leitura de cada comparável com similaridade, diferença de km, aderência regional, distância de mercado e impacto na análise.
- `negotiation_intelligence`: venda rápida, faixa ideal de anúncio, piso/teto de negociação e tempo estimado.
- `market_temperature_detail`: leitura textual da temperatura do mercado.
- `regional_explanation`: explicação do comportamento regional.
- `executive_market_insight`: resumo consultivo para o laudo.

A lógica não cria números aleatórios: ela deriva dos comparáveis, dispersão, liquidez, região, confiança e tendências calculadas pelos motores existentes. Quando a base real é pequena, a análise assume leitura exploratória e informa a limitação.

## MCV Market Intelligence Engine

A versão atual adiciona uma camada consultiva sobre o valuation existente, sem substituir a engine de preço nem o catálogo FIPE. O objetivo é transformar o laudo em uma leitura comercial acionável para venda do veículo.

Camadas adicionadas:

- **Selling Strategy Engine**: define preço inicial recomendado, faixa segura, venda rápida, teto provável, risco de supervalorização e recomendação de ajuste.
- **Price Positioning Engine**: mede a posição do preço frente aos comparáveis, competitividade, pressão de preço e resistência do mercado.
- **Buyer Behavior Engine**: traduz sinais regionais, quilometragem e posição de preço em leitura de comportamento comprador.
- **Market Insight Engine**: gera resumo executivo, temperatura de mercado e bullets comerciais derivados dos comparáveis e da liquidez.
- **Liquidity Pressure Engine**: adiciona pressão de liquidez, probabilidade estimada de venda e resistência acima da faixa recomendada.

Todos os insights são derivados dos dados disponíveis: comparáveis, dispersão, liquidez, regionalização, confiança da amostra e negociação calculada. A camada não cria tendências externas falsas e mantém fallback seguro quando a amostra é limitada.

## Estratégia de Venda — consultoria automotiva

Esta versão adiciona a camada de **Estratégia de Venda** como produto principal do Meu Carro Vale, sem substituir o valuation, o catálogo FIPE ou a inteligência de mercado existente.

O laudo agora ajuda o vendedor a responder perguntas práticas:

- por quanto anunciar;
- qual faixa aceitar para fechar negócio;
- qual valor evitar aceitar;
- acima de qual preço o veículo tende a perder liquidez;
- quando revisar o preço;
- como defender o valor usando comparáveis, liquidez e confiança da análise.

### Semáforo da Negociação

O painel possui uma simulação de proposta recebida. O usuário informa o valor oferecido e o sistema classifica em:

- **Boa proposta**: dentro ou acima da faixa ideal;
- **Negociar com cuidado**: ainda possível, mas abaixo da faixa ideal;
- **Proposta abaixo do recomendado**: risco de deixar dinheiro na mesa.

### Defesa do preço

A seção **Como defender esse valor** gera argumentos comerciais derivados dos dados disponíveis:

- quantidade e qualidade dos comparáveis;
- liquidez regional;
- dispersão de preços;
- sensibilidade à quilometragem;
- posição do veículo frente aos anúncios semelhantes.

### Risco de ficar parado

A análise também retorna o **Risco de ficar parado**, combinando demanda, pressão de preço, dispersão, confiança e quantidade de comparáveis. Essa leitura orienta quando manter o preço e quando revisar a estratégia.

A implementação principal fica em:

```text
backend/app/intelligence/sales/selling_decision_engine.py
```

E os campos principais retornados são:

```text
listing_price
ideal_close_range_min
ideal_close_range_max
minimum_recommended_price
resistance_price
stuck_risk_level
stuck_risk_reason
review_price_after_days
suggested_price_cut_percent
negotiation_signal
negotiation_message
price_defense_arguments
seller_summary
```

## Integração oficial com o `mcv-data-engine`

O Meu Carro Vale agora possui uma ponte oficial para consumir os contratos/exportações do projeto separado `mcv-data-engine`, sem misturar coleta ou scraping dentro do frontend/backend principal.

### Exports consumidos

Configure o caminho dos exports:

```env
USE_DATA_ENGINE_EXPORTS=true
MCV_DATA_ENGINE_EXPORTS_PATH=../mcv-data-engine/exports
```

A aplicação valida e consome:

- `manifest.json`
- `comparables.parquet` ou `comparables.csv`
- `liquidity.parquet` ou `liquidity.csv`
- `market_behavior.parquet` ou `market_behavior.csv`
- `snapshots.parquet` ou `snapshots.csv`

### Contrato de dados

A camada `backend/app/data_engine_bridge/` valida schema, colunas obrigatórias, arquivos vazios e tipos numéricos mínimos antes de usar os dados no valuation. Se os exports estiverem ausentes, inválidos ou sem amostra compatível para o veículo, o sistema mantém fallback seguro para o valuation já existente.

### Prioridade no valuation

Quando houver dados reais válidos do `mcv-data-engine`, o valuation usa os exports como fonte principal para:

- comparáveis oficiais;
- liquidez;
- comportamento de mercado;
- snapshots de preço;
- faixa recomendada;
- estratégia de venda;
- explicabilidade do laudo.

Isso reduz dependência de heurística interna e transforma o valuation em uma leitura baseada no motor real de dados automotivos.

### Endpoints de diagnóstico

Com autenticação ativa:

```http
GET /api/market/data-engine/status
GET /api/market/data-engine/manifest
```

Esses endpoints mostram disponibilidade, status de validação, manifest e schemas carregados.

### Dependências adicionais

O backend agora usa `pandas` e `pyarrow` para leitura de CSV/Parquet dos exports oficiais.

## Camada SaaS comercial

Esta versão adiciona uma camada SaaS real sem alterar o motor de valuation, o catálogo FIPE, a ponte com o `mcv-data-engine` ou a identidade visual aprovada.

### Recursos adicionados

- Cadastro, entrada, saída e sessão persistente com JWT e token de atualização.
- Hash seguro de senha com `passlib`.
- Estrutura multi-tenant com `tenants`, `users`, `tenant_users` e papéis.
- Papéis previstos: `admin`, `owner`, `analyst` e `user`.
- Histórico de avaliações por conta.
- Tela “Meus Laudos” com valor recomendado, liquidez, confiança e status.
- Tela “Meus Veículos” com histórico dos veículos avaliados.
- Planos e limites de uso por tenant.
- Camada `billing/` preparada para Mercado Pago e Stripe, sem cobrança real sem credenciais.
- Admin interno básico para operação.
- Isolamento obrigatório por `tenant_id` nas consultas de laudos e veículos.

### Fluxo principal

1. Criar conta em “Criar conta”.
2. Entrar com e-mail e senha.
3. Cadastrar o veículo no painel.
4. Gerar a análise.
5. O sistema salva veículo, laudo, resultado do valuation, estratégia de venda, comparáveis, liquidez e confiança.
6. Consultar o histórico em “Meus Laudos” e “Meus Veículos”.

### Variáveis importantes

```env
DATABASE_URL=sqlite:///./meu_carro_vale.db
JWT_SECRET=troque-em-producao
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=14
MCV_DATA_ENGINE_EXPORTS_PATH=../mcv-data-engine/exports
```

### Banco e migração

Para ambiente local, o backend cria as tabelas com `Base.metadata.create_all()` ao iniciar.
Para produção/Postgres, a migration `0007_saas_commercial_layer.py` cria as tabelas SaaS.

### Endpoints principais

- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/refresh`
- `POST /api/auth/logout`
- `GET /api/auth/me`
- `GET /api/saas/meu-painel`
- `GET /api/saas/meus-veiculos`
- `GET /api/saas/meus-laudos`
- `GET /api/saas/plano-atual`
- `GET /api/saas/planos`
- `POST /api/saas/billing/checkout`

### Validação

Comandos usados nesta entrega:

```bash
cd backend && pip install -r requirements.txt
cd .. && pytest backend/tests
cd frontend && npm install && npm run build
python -m compileall backend/app
```

## Integração final com mcv-data-engine

O Meu Carro Vale agora consome oficialmente o `mcv-data-engine` para busca viva e avaliação automática.

Portas locais recomendadas:

- Frontend Meu Carro Vale: `http://127.0.0.1:5180`
- Backend Meu Carro Vale: `http://127.0.0.1:8010`
- API mcv-data-engine: `http://127.0.0.1:8020`

Variáveis principais:

```env
MCV_DATA_ENGINE_MODE=api
MCV_DATA_ENGINE_API_URL=http://127.0.0.1:8020
MCV_DATA_ENGINE_EXPORTS_PATH=../mcv-data-engine/exports
```

Modos de integração:

- `api`: usa endpoints do `mcv-data-engine`, como `/catalog/search`, `/market/comparables`, `/market/liquidity`, `/market/behavior` e `/market/snapshots`.
- `files`: lê os exports locais em Parquet/CSV, incluindo `comparables`, `liquidity`, `market_behavior`, `snapshots` e `manifest`.

Fluxo principal:

1. O usuário digita algo como `Agile LTZ 2013`.
2. O backend consulta o catálogo do `mcv-data-engine`.
3. O frontend mostra sugestões com marca, modelo, versão, ano, combustível e código FIPE quando disponível.
4. Ao avaliar, o endpoint `/api/vehicles/auto-valuate` resolve o veículo, busca comparáveis, liquidez, comportamento de mercado e snapshots.
5. O valuation usa dados reais quando a amostra está disponível.
6. Quando não há dados suficientes, o sistema usa fallback seguro e sinaliza amostra limitada.
7. O laudo é salvo no tenant do usuário autenticado.

Comandos úteis:

```bash
# Data engine
cd mcv-data-engine
uvicorn api.main:app --host 127.0.0.1 --port 8020
python -m vehicle_catalog.fipe_incremental_sync --type carros --max-brands 1 --max-models 1

# Meu Carro Vale backend
cd meu-carro-vale
uvicorn backend.app.main:app --host 127.0.0.1 --port 8010

# Meu Carro Vale frontend
cd meu-carro-vale/frontend
npm install
npm run dev
```
