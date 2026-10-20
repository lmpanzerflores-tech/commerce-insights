"""Analytics API from the real, anonymized Olist Brazilian E-Commerce dataset."""
from pathlib import Path
from functools import lru_cache
from datetime import datetime
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
FILES = {
    "orders": "olist_orders_dataset.csv",
    "items": "olist_order_items_dataset.csv",
    "products": "olist_products_dataset.csv",
    "customers": "olist_customers_dataset.csv",
}
app = FastAPI(title="Commerce Insights API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], allow_methods=["GET"], allow_headers=["*"])

@lru_cache(maxsize=1)
def load_data():
    missing = [n for n in FILES.values() if not (DATA / n).exists()]
    if missing:
        raise FileNotFoundError("Arquivos ausentes em data/: " + ", ".join(missing))
    orders = pd.read_csv(DATA / FILES["orders"], usecols=["order_id", "customer_id", "order_status", "order_purchase_timestamp"])
    items = pd.read_csv(DATA / FILES["items"], usecols=["order_id", "product_id", "price"])
    products = pd.read_csv(DATA / FILES["products"], usecols=["product_id", "product_category_name"])
    customers = pd.read_csv(DATA / FILES["customers"], usecols=["customer_id", "customer_state"])
    orders["order_purchase_timestamp"] = pd.to_datetime(orders["order_purchase_timestamp"], errors="coerce")
    # Receita comercial reconhecida aqui apenas para pedidos entregues; frete fora da métrica.
    delivered = orders.loc[orders["order_status"] == "delivered"]
    df = (items.merge(delivered, on="order_id", how="inner")
               .merge(products, on="product_id", how="left")
               .merge(customers, on="customer_id", how="left"))
    df["price"] = pd.to_numeric(df["price"], errors="coerce").fillna(0)
    df["product_category_name"] = df["product_category_name"].fillna("Sem categoria").str.replace("_", " ", regex=False).str.title()
    df["customer_state"] = df["customer_state"].fillna("ND")
    df = df.dropna(subset=["order_purchase_timestamp"])
    return df

def to_money(v):
    return round(float(v), 2)

def filtered(df, start, end, state):
    if start:
        try: dt = pd.Timestamp(start)
        except Exception: raise HTTPException(422, "Data inicial inválida")
        df = df.loc[df["order_purchase_timestamp"] >= dt]
    if end:
        try: dt = pd.Timestamp(end)
        except Exception: raise HTTPException(422, "Data final inválida")
        df = df.loc[df["order_purchase_timestamp"] < dt + pd.Timedelta(days=1)]
    if state and state != "ALL":
        df = df.loc[df["customer_state"] == state]
    return df

@app.get("/api/health")
def health():
    return {"status": "ok", "dataset_loaded": not any(not (DATA / p).exists() for p in FILES.values())}

@app.get("/api/filters")
def filters():
    try: df = load_data()
    except FileNotFoundError as exc: raise HTTPException(503, str(exc))
    return {"states": sorted(df["customer_state"].unique().tolist()),
            "min_date": df["order_purchase_timestamp"].min().date().isoformat(),
            "max_date": df["order_purchase_timestamp"].max().date().isoformat()}

@app.get("/api/dashboard")
def dashboard(start: str | None = Query(None), end: str | None = Query(None), state: str = Query("ALL")):
    try: df = load_data()
    except FileNotFoundError as exc: raise HTTPException(503, str(exc))
    df = filtered(df, start, end, state)
    revenue = to_money(df["price"].sum())
    orders = int(df["order_id"].nunique())
    items = int(len(df))
    ticket = to_money(revenue / orders) if orders else 0
    monthly = (df.assign(month=df["order_purchase_timestamp"].dt.to_period("M").astype(str))
                 .groupby("month", as_index=False).agg(revenue=("price", "sum"), orders=("order_id", "nunique"))
                 .sort_values("month"))
    categories = (df.groupby("product_category_name", as_index=False)
                    .agg(revenue=("price", "sum"), items=("product_id", "size"))
                    .sort_values("revenue", ascending=False).head(8))
    products = (df.groupby("product_id", as_index=False)
                  .agg(items=("product_id", "size"), revenue=("price", "sum"))
                  .sort_values(["items", "revenue"], ascending=False).head(10))
    states = (df.groupby("customer_state", as_index=False)
                .agg(revenue=("price", "sum"), orders=("order_id", "nunique"))
                .sort_values("revenue", ascending=False).head(10))
    return {
        "kpis": {"revenue": revenue, "orders": orders, "items": items, "ticket": ticket},
        "monthly": [{"month": x.month, "revenue": to_money(x.revenue), "orders": int(x.orders)} for x in monthly.itertuples(index=False)],
        "categories": [{"name": x.product_category_name, "revenue": to_money(x.revenue), "items": int(x.items)} for x in categories.itertuples(index=False)],
        "products": [{"id": x.product_id, "items": int(x.items), "revenue": to_money(x.revenue)} for x in products.itertuples(index=False)],
        "states": [{"name": x.customer_state, "revenue": to_money(x.revenue), "orders": int(x.orders)} for x in states.itertuples(index=False)],
        "data_note": "Pedidos com status delivered. Receita = soma dos preços dos itens, sem frete, por data da compra. Dados históricos reais e anonimizados (2016–2018)."
    }
