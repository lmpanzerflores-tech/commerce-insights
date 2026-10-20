# Commerce Insights | Dashboard de Vendas Reais

Projeto de portfólio full stack com React, Recharts, FastAPI e pandas. O frontend consulta uma API REST que processa pedidos históricos **reais e anonimizados** da Olist.

## Fonte de dados
Baixe [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) e extraia os arquivos abaixo para `data/`:

- `olist_orders_dataset.csv`
- `olist_order_items_dataset.csv`
- `olist_products_dataset.csv`
- `olist_customers_dataset.csv`

O dataset contém pedidos históricos de 2016 a 2018, NÃO dados em tempo real. Seus produtos são anonimizados, portanto o ranking usa SKU/ID em vez de nomes inventados.

## Executar a API

```bash
cd backend
python -m venv .venv
# Windows (PowerShell): .venv\\Scripts\\Activate.ps1
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Endpoints: `GET /api/health`, `GET /api/filters`, `GET /api/dashboard?start=2017-01-01&end=2018-08-31&state=SP`. Documentação interativa: `http://localhost:8000/docs`.

## Executar frontend (outro terminal)

```bash
cd frontend
npm install
npm run dev
```

Abra `http://localhost:5173`.

## Definições dos indicadores

- Consideram-se apenas pedidos com status `delivered`.
- Faturamento: soma de `price` dos itens, sem incluir frete. É uma métrica operacional simplificada, não receita contábil auditada.
- Pedidos: contagem distinta de `order_id`.
- Unidades: contagem de itens nas linhas de `order_items`.
- Ticket médio: faturamento dividido pelo número de pedidos distintos.
- As séries são agrupadas pela data da **compra** de pedidos que foram entregues. Os filtros usam essa mesma data e o estado do comprador.

## Funcionalidades
Cards de KPIs, área temporal mensal interativa, ranking de categorias, top 10 produtos, receita por UF, filtros de data e estado, interface responsiva e documentação Swagger.

## Evoluções sugeridas
Autenticação, comparação com período anterior, cache e testes automatizados, banco PostgreSQL e pipeline de ingestão, exportação CSV, deploy frontend e API, CI no GitHub Actions.

## Licenciamento de dados
Consulte os termos do dataset na página oficial do Kaggle antes de redistribuí-lo. Este repositório não distribui os CSVs originais.
