import os
import pandas as pd
from db import engine

os.makedirs("dashboard_data", exist_ok=True)

state_names = {
    "AC": "Acre", "AL": "Alagoas", "AP": "Amapa", "AM": "Amazonas", "BA": "Bahia",
    "CE": "Ceara", "DF": "Distrito Federal", "ES": "Espirito Santo", "GO": "Goias",
    "MA": "Maranhao", "MT": "Mato Grosso", "MS": "Mato Grosso do Sul", "MG": "Minas Gerais",
    "PA": "Para", "PB": "Paraiba", "PR": "Parana", "PE": "Pernambuco", "PI": "Piaui",
    "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte", "RS": "Rio Grande do Sul",
    "RO": "Rondonia", "RR": "Roraima", "SC": "Santa Catarina", "SP": "Sao Paulo",
    "SE": "Sergipe", "TO": "Tocantins",
}

monthly = pd.read_sql("""
    SELECT
        DATE_TRUNC('month', o.order_purchase_timestamp)::date AS month,
        COUNT(DISTINCT o.order_id) AS orders,
        ROUND(SUM(oi.price), 2) AS revenue
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE o.order_status = 'delivered'
      AND o.order_purchase_timestamp >= '2017-01-01'
      AND o.order_purchase_timestamp < '2018-09-01'
    GROUP BY 1
    ORDER BY 1
""", engine)

category = pd.read_sql("""
    SELECT
        COALESCE(t.product_category_name_english, 'unknown') AS category,
        COUNT(DISTINCT oi.order_id) AS orders,
        ROUND(SUM(oi.price), 2) AS revenue
    FROM order_items oi
    JOIN orders o ON oi.order_id = o.order_id
    JOIN products p ON oi.product_id = p.product_id
    LEFT JOIN category_translation t ON p.product_category_name = t.product_category_name
    WHERE o.order_status = 'delivered'
    GROUP BY 1
    ORDER BY revenue DESC
""", engine)

state_sales = pd.read_sql("""
    SELECT
        c.customer_state AS state,
        COUNT(DISTINCT o.order_id) AS orders,
        ROUND(SUM(oi.price), 2) AS revenue
    FROM orders o
    JOIN customers c ON o.customer_id = c.customer_id
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY 1
""", engine)

state_delivery = pd.read_sql("""
    SELECT
        customer_state AS state,
        ROUND(AVG(delivery_days), 1) AS avg_delivery_days,
        ROUND(100.0 * COUNT(*) FILTER (WHERE delay_days > 0) / COUNT(*), 1) AS late_pct,
        ROUND(AVG(review_score), 2) AS avg_review
    FROM order_delivery
    GROUP BY 1
""", engine)

states = state_sales.merge(state_delivery, on="state")
states["state_name"] = states["state"].map(state_names)
states["revenue_share_pct"] = (100 * states["revenue"] / states["revenue"].sum()).round(1)
states = states.sort_values("revenue", ascending=False)

segments = pd.read_sql("""
    SELECT
        segment,
        COUNT(*) AS customers,
        ROUND(SUM(monetary), 2) AS revenue,
        ROUND(AVG(monetary), 2) AS avg_spend
    FROM rfm_customers
    GROUP BY segment
    ORDER BY revenue DESC
""", engine)

delivery = pd.read_sql("""
    SELECT
        CASE
            WHEN delay_days <= 0 THEN '1. On time or early'
            WHEN delay_days <= 3 THEN '2. Late 1-3 days'
            WHEN delay_days <= 7 THEN '3. Late 4-7 days'
            WHEN delay_days <= 14 THEN '4. Late 8-14 days'
            ELSE '5. Late 15+ days'
        END AS delay_bucket,
        COUNT(*) AS orders,
        ROUND(AVG(review_score), 2) AS avg_review,
        ROUND(100.0 * COUNT(*) FILTER (WHERE review_score <= 2) / COUNT(*), 1) AS bad_review_pct
    FROM order_delivery
    GROUP BY 1
    ORDER BY 1
""", engine)

tables = {
    "monthly_revenue": monthly,
    "category_revenue": category,
    "state_performance": states,
    "rfm_segments": segments,
    "delivery_vs_reviews": delivery,
}

for name, df in tables.items():
    df.to_csv(f"dashboard_data/{name}.csv", index=False)
    print(name, len(df))
