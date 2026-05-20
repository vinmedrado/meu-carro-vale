# Arquitetura

Pipeline principal:

1. coletar dados;
2. parsear;
3. normalizar;
4. validar qualidade;
5. deduplicar;
6. salvar anúncios;
7. gerar snapshots;
8. calcular liquidez;
9. exportar datasets para o Meu Carro Vale.

Camadas:

- `collectors/`: conectores de fontes de dados;
- `parsers/`: importação CSV/JSON e parsers por fonte;
- `normalizers/`: padronização de marca, modelo, versão, km, preço e localização;
- `deduplication/`: identificação de duplicados por URL, hash e similaridade;
- `snapshots/`: agregações históricas por veículo/região/data;
- `liquidity/`: indicadores de volume, dispersão, saturação e pressão de mercado;
- `comparables/`: dataset limpo para valuation;
- `storage/`: modelos, repositório e exportação;
- `api/`: API futura para consumo direto pelo Meu Carro Vale.
