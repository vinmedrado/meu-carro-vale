# mcv-data-engine

Motor de dados real do **Meu Carro Vale**. Este projeto é separado do produto principal e tem uma função clara: receber, normalizar, validar, deduplicar, agregar e exportar dados automotivos para alimentar valuation, comparáveis, liquidez e inteligência regional.

## Papel no ecossistema Meu Carro Vale

O **Meu Carro Vale** continua sendo o produto de valuation e consultoria de venda. O **mcv-data-engine** é a infraestrutura de dados: coleta responsável, ingestão estruturada, qualidade, snapshots, liquidez e exports.

## O que esta versão entrega

- Coletor FIPE preservado.
- Coletores preparados para OLX, Webmotors, iCarros, Mercado Livre e Kavak em modo seguro.
- Ingestão real via CSV, JSON e lotes.
- Processamento em chunks para arquivos grandes.
- Normalização automotiva com aliases e heurísticas.
- Motor de qualidade de dados.
- Deduplicação com `duplicate_confidence_score`.
- Snapshots evoluídos por modelo, versão, ano e região.
- Liquidez com saturação, pressão, dispersão, estabilidade e velocidade estimada.
- Comparable Intelligence Engine com score 0 a 100, explicação e impacto no preço.
- Dataset de comparáveis inteligentes para o Meu Carro Vale.
- API FastAPI expandida.
- Painel operacional interno em Streamlit.
- Exports em CSV e Parquet quando `pyarrow` está disponível.

## Estrutura

```text
mcv-data-engine/
  api/                         # API FastAPI
  collectors/                  # FIPE real + coletores preparados
  comparables/                 # dataset e inteligência de comparáveis
  config/                      # configurações e .env
  dashboard/                   # painel operacional interno
  deduplication/               # deduplicação e republicação
  ingestion/                   # CSV, JSON, API futura, batch e validações
  liquidity/                   # cálculos de liquidez
  normalizers/                 # padronização automotiva
  snapshots/                   # agregações históricas
  storage/                     # modelos, repositório e exports
  tests/                       # testes básicos
```

## Instalação

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

## Banco de dados

O projeto usa PostgreSQL como destino principal, mas mantém compatibilidade com SQLite para desenvolvimento local.

```bash
python cli.py init-db
```

Configure no `.env`:

```env
DATABASE_URL=sqlite:///mcv_data_engine.db
# ou PostgreSQL:
# DATABASE_URL=postgresql+psycopg2://usuario:senha@localhost:5432/mcv_data_engine
```

## Ingestão CSV

```bash
python cli.py import sample_market_listings.csv
python cli.py import sample_market_listings.csv --persist
```

Formato recomendado:

```csv
marca,modelo,versao,ano,km,preco,cidade,estado,fonte,url,combustivel,cambio,vendedor_tipo
Toyota,Corolla,XEI,2020,42000,115000,São Paulo,SP,CSV,http://exemplo/1,Flex,CVT,loja
```

## Ingestão em lote

```bash
python cli.py batch-import base_olx.csv base_webmotors.json --persist
```

## API

```bash
uvicorn api.main:app --reload --port 8020
```

Endpoints principais:

- `POST /ingestion/csv`
- `POST /ingestion/json`
- `POST /ingestion/batch`
- `GET /market/listings`
- `GET /market/comparables`
- `GET /market/liquidity`
- `GET /market/snapshots`
- `GET /market/quality`

## Painel operacional

```bash
streamlit run dashboard/operational_dashboard.py
```

Mostra quantidade de anúncios, duplicados, qualidade média, snapshots e exports gerados.

## Qualidade dos dados

O `DataQualityEngine` calcula:

- nota de qualidade do anúncio;
- campos obrigatórios ausentes;
- preço suspeito;
- quilometragem inválida;
- região inconsistente;
- status de normalização.

## Normalização automotiva

A normalização padroniza campos como:

- `Corolla XEI`, `Corolla XEi`, `Corolla XEI 2.0`, `Corolla XEI Flex CVT`;
- marca, modelo e versão;
- combustível;
- câmbio;
- preço e quilometragem.

## Deduplicação

Detecta:

- mesma URL;
- mesmo hash de similaridade;
- mesma placa parcial quando disponível;
- republicação provável;
- mesmo veículo em múltiplas fontes.

Retorna `duplicate_confidence_score`.

## Comparable Intelligence Engine

O coração desta versão é o motor `comparables/comparable_intelligence_engine.py`. Ele compara cada veículo com anúncios reais e calcula um score de similaridade de 0 a 100 usando:

- marca/modelo: 35%;
- versão: 20%;
- ano: 15%;
- quilometragem: 15%;
- região: 10%;
- qualidade e recência: 5%.

Classificação:

- `Excelente`;
- `Bom`;
- `Médio`;
- `Fraco`.

Cada comparável retorna:

- `comparable_score`;
- `match_quality`;
- `price_delta`;
- `km_delta`;
- `year_delta`;
- `regional_match`;
- `explanation`;
- `price_impact`.

Exemplo de explicação:

> Comparável excelente: mesma marca e modelo, versão compatível, mesmo ano, quilometragem semelhante, região compatível.

Exemplo de impacto:

> pressiona preço para cima

Isso permite que o Meu Carro Vale mostre não apenas o preço, mas a evidência usada na formação da faixa recomendada, estratégia de venda, liquidez e laudo.

## API de comparáveis

```bash
GET /market/comparables?brand=Toyota&model=Corolla&version=XEI&year=2021&mileage=42000&state=SP&city=São Paulo&limit=20
```

Também aceita parâmetros em português: `marca`, `modelo`, `versao`, `ano`, `km`, `estado`, `cidade`.

A resposta traz:

- lista de comparáveis ranqueados;
- score;
- explicação;
- impacto no preço;
- outliers removidos;
- estatísticas da amostra: mínimo, P25, mediana, P75, máximo, dispersão e confiança.

## Exports de comparáveis

O pipeline gera:

- `exports/comparables.csv`;
- `exports/comparables.parquet` quando `pyarrow` estiver disponível.

Campos principais:

- `vehicle_id`;
- `comparable_id`;
- `score`;
- `match_quality`;
- `price_delta`;
- `km_delta`;
- `year_delta`;
- `regional_match`;
- `explanation`;
- `price_impact`.

## Snapshots e liquidez

Os snapshots agregam:

- preço médio;
- mediana;
- percentis P10/P25/P75/P90;
- dispersão;
- liquidez;
- temperatura de mercado;
- semana e mês.

A liquidez calcula:

- saturação;
- pressão de mercado;
- volume regional;
- estabilidade;
- velocidade estimada de venda.

## Exports

Arquivos gerados em `exports/`:

- `market_listings.csv/parquet`
- `market_snapshots.csv/parquet`
- `snapshots.csv/parquet`
- `liquidity.csv/parquet`
- `comparables.csv/parquet` — comparáveis inteligentes com score, explicação e impacto
- `comparables_base.csv/parquet` — base de comparáveis limpa anterior
- `normalized_catalog.csv/parquet`
- `market_quality.csv/parquet`

## Coleta responsável

Este projeto não faz scraping agressivo. As fontes externas devem respeitar:

- termos de uso;
- robots.txt;
- limites de requisição;
- user-agent configurável;
- backoff;
- logs;
- cache;
- modo seguro.

Coletores avançados devem ser ativados apenas quando houver permissão técnica e jurídica.

## Testes

```bash
pytest
python -m compileall .
```

## Roadmap

- Jobs recorrentes com agendamento.
- API autenticada para o Meu Carro Vale consumir exports.
- Integração formal com bases autorizadas.
- Feature store para modelos de valuation, liquidez e negociação.
- Monitoramento de drift de mercado por região.

## Market Behavior Engine

A camada `market_behavior/` transforma os comparáveis limpos em leitura de comportamento de mercado automotivo. Ela não usa análise de fotos/imagens e não calcula comportamento em cima de anúncios brutos: o fluxo recomendado é:

`ingestão → normalização → qualidade → deduplicação → comparáveis limpos → comportamento de mercado → exports/API`

### O que a engine calcula

- **Pressão de preço**: mede dispersão, volume de oferta, concentração abaixo/acima da mediana e distância do preço informado contra a amostra.
- **Velocidade de mercado**: estima giro a partir de recência dos anúncios, volume e estabilidade dos snapshots.
- **Resistência de preço**: identifica teto provável e ponto em que o anúncio começa a perder competitividade.
- **Comportamento regional**: compara cidade/estado contra a amostra ampliada para indicar região valorizada, alinhada ou descontada.
- **Tendência**: usa snapshots históricos para classificar valorização, queda, estabilidade ou volatilidade.
- **Risco de ficar parado**: combina pressão de preço, baixa velocidade e resistência acima da faixa competitiva.
- **Resumo executivo**: gera uma frase operacional para alimentar o Meu Carro Vale com leitura consultiva.

### Endpoints adicionados

```text
GET /market/behavior
GET /market/price-pressure
GET /market/velocity
GET /market/resistance
GET /market/regional-behavior
GET /market/trends
```

Parâmetros principais:

```text
brand, model, version, year, mileage, state, city, preco, limit
```

Também são aceitos aliases em português em alguns fluxos (`marca`, `modelo`, `versao`, `ano`, `km`, `estado`, `cidade`).

### Export adicionado

Ao rodar o pipeline de ingestão, o projeto agora gera:

```text
exports/market_behavior.csv
exports/market_behavior.parquet
```

Campos principais:

```text
brand, model, version, year, state, city,
pressure_level, velocity_level, resistance_price,
trend_direction, stuck_risk_level, regional_strength, summary
```

### Integração com Meu Carro Vale

O Meu Carro Vale pode consumir essa camada para enriquecer:

- valuation;
- estratégia de venda;
- laudo consultivo;
- liquidez;
- negociação;
- explicabilidade;
- risco de ficar parado.

A leitura é sempre derivada dos dados disponíveis: comparáveis limpos, snapshots, dispersão, volume, região e recência. Quando a amostra é pequena, a API retorna baixa amostra/indefinição em vez de inventar tendência.

## Pipeline operacional e contrato de dados

Esta versão consolida o `mcv-data-engine` como infraestrutura operacional para alimentar o Meu Carro Vale com dados consistentes, auditáveis e prontos para consumo.

### Comando único

Execute o pipeline completo com:

```bash
python -m jobs.run_all
```

Fluxo executado:

1. ingestão
2. validação
3. normalização
4. deduplicação
5. snapshots
6. comparáveis
7. liquidez
8. comportamento de mercado
9. exports
10. validação final

Também é possível informar um arquivo CSV/JSON:

```bash
python -m jobs.run_all --input caminho/arquivo.csv
```

### Execução parcial

```bash
python -m jobs.run_all --only snapshots
python -m jobs.run_all --only comparables
python -m jobs.run_all --only liquidity
python -m jobs.run_all --only behavior
python -m jobs.run_all --only exports
python -m jobs.run_all --only final_validation
```

A execução parcial reaproveita o pipeline de ingestão quando necessário e sempre pode finalizar com validação dos exports.

### Contrato de dados

Os contratos oficiais ficam em:

```text
contracts/export_contracts.py
```

Exports padronizados:

- `comparables.parquet/csv`
- `liquidity.parquet/csv`
- `market_behavior.parquet/csv`
- `snapshots.parquet/csv`
- `normalized_catalog.parquet/csv`

Cada contrato define colunas obrigatórias, tipos esperados, faixas válidas e versão de schema.

### Validação dos exports

O validador fica em:

```text
validation/export_validation_engine.py
```

Ele verifica:

- existência dos arquivos;
- arquivo vazio;
- schema oficial;
- colunas obrigatórias;
- preços e scores válidos;
- datas e valores extremos;
- duplicidades em chaves conhecidas.

### Manifest operacional

Após o pipeline, o arquivo abaixo é gerado:

```text
exports/manifest.json
```

Ele contém:

- data de geração;
- arquivos gerados;
- quantidade de registros;
- versão de schema;
- qualidade média;
- snapshots disponíveis;
- status de validação.

### Logs operacionais

Cada execução grava um resumo em:

```text
logs/pipeline/pipeline_<data>.json
```

Os logs registram etapas, duração, status, métricas, erros e caminho do manifesto.

### API operacional

Endpoints adicionados:

```text
POST /ops/pipeline/run
GET  /ops/exports/validate
GET  /ops/exports/manifest
```

Esses endpoints permitem disparar pipeline, validar exports e gerar manifesto para integração futura com o Meu Carro Vale.

### Integração com Meu Carro Vale

O contrato foi pensado para leitura simples com Pandas/Polars:

```python
import pandas as pd

comparaveis = pd.read_parquet("exports/comparables.parquet")
liquidez = pd.read_parquet("exports/liquidity.parquet")
comportamento = pd.read_parquet("exports/market_behavior.parquet")
```

O Meu Carro Vale pode consumir esses arquivos como fonte confiável para valuation, estratégia de venda, liquidez, comportamento regional e laudo executivo.

## Catálogo Mestre FIPE

O `mcv-data-engine` agora possui um catálogo mestre nacional baseado na FIPE, separado do pipeline de anúncios e preparado para uso incremental.

### O que o catálogo cobre

- Carros, motos e caminhões.
- Marcas, modelos, anos, versões, códigos FIPE, combustível, mês de referência e valor FIPE.
- Deduplicação por chave oficial FIPE.
- Normalização de nomes e aliases brasileiros, como `GM → Chevrolet`, `VW → Volkswagen`, `S-10 → S10`, `HRV → HR-V` e `TCross → T-Cross`.
- Índice de busca para consultas como `Agile LTZ 2013`.

### Comandos

Sincronização completa manual:

```bash
python -m vehicle_catalog.fipe_full_sync
```

Sincronização incremental:

```bash
python -m vehicle_catalog.fipe_incremental_sync
```

Amostra segura para validação local:

```bash
python -m vehicle_catalog.fipe_incremental_sync --type carros --max-brands 1 --max-models 1
```

Pipeline operacional com catálogo incremental:

```bash
python -m jobs.run_all
```

Execução parcial do catálogo:

```bash
python -m jobs.run_all --only catalog
```

### Contrato de deduplicação

- Marca: `vehicle_type + fipe_brand_code`
- Modelo: `vehicle_type + brand_id + fipe_model_code`
- Versão: `vehicle_type + model_id + fipe_year_code + fipe_code`

Rodar a sincronização novamente não duplica registros. Quando a FIPE muda o preço ou o mês de referência, o registro existente é atualizado.

### Checkpoint e segurança

A sincronização salva progresso em `logs/pipeline/fipe_catalog_checkpoint.json`. A coleta usa pausa entre requisições, retry/backoff via cliente responsável e modo seguro configurável por `.env`.

Variáveis principais:

```env
FIPE_SYNC_SLEEP_SECONDS=0.25
FIPE_SYNC_TIMEOUT_SECONDS=20
FIPE_SYNC_MAX_RETRIES=3
FIPE_SYNC_ENABLE_CARROS=true
FIPE_SYNC_ENABLE_MOTOS=true
FIPE_SYNC_ENABLE_CAMINHOES=true
FIPE_SYNC_MARK_MISSING_INACTIVE=false
```

### Exports do catálogo

São gerados CSV e Parquet quando `pyarrow` está disponível:

- `exports/vehicle_brands.*`
- `exports/vehicle_models.*`
- `exports/vehicle_versions.*`
- `exports/vehicle_catalog_full.*`
- `exports/vehicle_search_index.*`
- `exports/catalog_manifest.json`

### API do catálogo

- `GET /catalog/brands`
- `GET /catalog/models`
- `GET /catalog/versions`
- `GET /catalog/search?q=Agile LTZ 2013`
- `GET /catalog/sync/status`
- `POST /catalog/sync/full`
- `POST /catalog/sync/incremental`

### Integração com Meu Carro Vale

O catálogo mestre alimenta seleção de veículos, validação de modelo/versão, enriquecimento por código FIPE e geração de bases consistentes para valuation, comparáveis, liquidez e comportamento de mercado.

## Robustez operacional da sincronização FIPE

A sincronização do Catálogo Mestre FIPE agora possui controles operacionais para rodar em produção com segurança.

### Modo teste controlado

Use limites para validar amostras pequenas antes de executar uma carga ampla:

```bash
python -m vehicle_catalog.fipe_incremental_sync --type carros --max-brands 1 --max-models 1 --max-versions 1
```

Parâmetros disponíveis:

- `--max-brands`: limita a quantidade de marcas.
- `--max-models`: limita modelos por marca.
- `--max-versions`: limita anos/versões por modelo.
- `--only-brands`: sincroniza somente marcas.
- `--only-models`: sincroniza marcas e modelos.
- `--only-versions`: processa versões com suporte a retomada.
- `--no-resume`: ignora checkpoint anterior.

### Proteção da full sync

A carga completa pode demorar bastante e gerar muitas requisições. Por isso, ela só roda com confirmação explícita:

```bash
python -m vehicle_catalog.fipe_full_sync --confirm-full-sync
```

Sem `--confirm-full-sync`, a execução é cancelada com mensagem amigável.

### Checkpoint e retomada

O progresso é salvo em:

```text
logs/pipeline/fipe_catalog_checkpoint.json
```

O checkpoint registra tipo, marca, modelo, versão, etapa atual, índices de progresso e timestamp. Se a execução cair, a próxima sincronização incremental pode retomar com segurança.

### Logs, ETA e progresso

Durante a execução, o sistema mostra:

- tipo atual;
- marca atual;
- modelo atual;
- progresso de versões;
- tempo decorrido;
- velocidade média;
- ETA aproximado por modelo.

### Exports automáticos

Ao finalizar qualquer sync, o sistema gera automaticamente:

- `exports/vehicle_brands.csv/parquet`
- `exports/vehicle_models.csv/parquet`
- `exports/vehicle_versions.csv/parquet`
- `exports/vehicle_catalog_full.csv/parquet`
- `exports/vehicle_search_index.csv/parquet`
- `exports/catalog_manifest.json`

### Manifest expandido

O `catalog_manifest.json` inclui status final, modo de execução, totais encontrados, totais persistidos, novos registros, atualizados, ignorados, erros, duração e mês de referência.

### Pipeline operacional

O pipeline normal continua usando sync incremental segura:

```bash
python -m jobs.run_all --only catalog
```

A full sync deve permanecer manual e confirmada.

## Consumo oficial pelo Meu Carro Vale

O data engine expõe contratos para o SaaS Meu Carro Vale por API e por arquivos.

Endpoints usados pelo SaaS:

- `GET /catalog/search?q=Agile%20LTZ%202013`
- `GET /market/comparables`
- `GET /market/liquidity`
- `GET /market/behavior`
- `GET /market/snapshots`
- `GET /ops/exports/manifest`

Exports usados em modo arquivo:

- `exports/comparables.parquet` ou `.csv`
- `exports/liquidity.parquet` ou `.csv`
- `exports/market_behavior.parquet` ou `.csv`
- `exports/snapshots.parquet` ou `.csv`
- `exports/manifest.json`
- `exports/vehicle_search_index.parquet` ou `.csv`, quando gerado pelo catálogo FIPE

Para rodar a API:

```bash
uvicorn api.main:app --host 127.0.0.1 --port 8020
```

---

## Sync FIPE resiliente contra erro 429

Esta versão mantém a sincronização incremental segura para rodar por longos períodos. Quando a API FIPE limita requisições, a execução não encerra tudo: ela reduz a velocidade, salva checkpoint, faz retentativas e preserva os itens pendentes em fila.

### Configuração recomendada

No arquivo `.env` do `mcv-data-engine`:

```env
FIPE_SYNC_BASE_SLEEP_SECONDS=1.5
FIPE_SYNC_MAX_RETRIES=6
FIPE_SYNC_BACKOFF_MULTIPLIER=3
FIPE_SYNC_MAX_BACKOFF_SECONDS=180
FIPE_SYNC_429_COOLDOWN_SECONDS=300
FIPE_SYNC_MAX_429_BEFORE_COOLDOWN=5
```

### Como rodar sync real

```bash
cd mcv-data-engine
python -m vehicle_catalog.fipe_incremental_sync --type carros
```

Para teste controlado:

```bash
python -m vehicle_catalog.fipe_incremental_sync --type carros --max-brands 5 --max-models 5 --max-versions 3
```

### Como retomar

A retomada é padrão. O checkpoint fica em:

```text
logs/pipeline/fipe_catalog_checkpoint.json
```

Para retomar normalmente, rode o mesmo comando de novo:

```bash
python -m vehicle_catalog.fipe_incremental_sync --type carros
```

Para ignorar retomada:

```bash
python -m vehicle_catalog.fipe_incremental_sync --type carros --no-resume
```

### Como lidar com 429

Quando a API limitar requisições, os logs mostram:

```text
Limite detectado
Aguardando X segundos
Retomando do checkpoint
Item enviado para retentativa
```

O comportamento é:

1. detecta 429;
2. espera 5s, 15s, 45s, 120s;
3. aumenta a pausa entre chamadas;
4. após vários 429 seguidos, faz cooldown global;
5. salva checkpoint;
6. envia versões pendentes para fila de retentativa;
7. continua sem encerrar a sync inteira.

A fila fica em:

```text
logs/pipeline/fipe_retry_queue.json
```

### Velocidade segura

O padrão é seguro, não rápido. Para reduzir risco de bloqueio:

```env
FIPE_SYNC_BASE_SLEEP_SECONDS=2.0
FIPE_SYNC_429_COOLDOWN_SECONDS=600
FIPE_SYNC_MAX_429_BEFORE_COOLDOWN=3
```

Para acelerar com risco maior:

```env
FIPE_SYNC_BASE_SLEEP_SECONDS=0.8
```

Use aceleração apenas em testes pequenos.

### Testes de robustez

```bash
cd mcv-data-engine
pytest -q tests/test_fipe_sync_robustness.py
```

Cobertura adicionada:

- retry em 429;
- backoff exponencial;
- cooldown global;
- checkpoint salvo antes da versão;
- item preservado na fila de retentativa.
