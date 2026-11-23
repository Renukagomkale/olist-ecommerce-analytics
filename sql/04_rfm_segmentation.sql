DROP TABLE IF EXISTS rfm_customers;

CREATE TABLE rfm_customers AS
WITH base AS (
    SELECT
        c.customer_unique_id,
        (SELECT MAX(order_purchase_timestamp)::date FROM orders) - MAX(o.order_purchase_timestamp)::date AS recency_days,
        COUNT(DISTINCT o.order_id) AS frequency,
        ROUND(SUM(oi.price), 2) AS monetary
    FROM customers c
    JOIN orders o ON c.customer_id = o.customer_id
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY c.customer_unique_id
),
scored AS (
    SELECT
        *,
        NTILE(5) OVER (ORDER BY recency_days DESC) AS r_score,
        CASE WHEN frequency = 1 THEN 1 WHEN frequency = 2 THEN 3 ELSE 5 END AS f_score,
        NTILE(5) OVER (ORDER BY monetary) AS m_score
    FROM base
)
SELECT
    *,
    CASE
        WHEN f_score >= 3 AND r_score >= 4 THEN 'Champions'
        WHEN f_score >= 3 THEN 'Loyal At Risk'
        WHEN r_score >= 4 AND m_score >= 4 THEN 'New High Value'
        WHEN r_score <= 2 AND m_score >= 4 THEN 'Lost High Value'
        ELSE 'One-time Buyers'
    END AS segment
FROM scored;

SELECT
    frequency AS orders_placed,
    COUNT(*) AS customers,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS customer_pct
FROM rfm_customers
GROUP BY frequency
ORDER BY frequency;

SELECT
    segment,
    COUNT(*) AS customers,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS customer_pct,
    ROUND(SUM(monetary), 2) AS revenue,
    ROUND(100.0 * SUM(monetary) / SUM(SUM(monetary)) OVER (), 1) AS revenue_pct,
    ROUND(AVG(monetary), 2) AS avg_spend
FROM rfm_customers
GROUP BY segment
ORDER BY revenue DESC;
