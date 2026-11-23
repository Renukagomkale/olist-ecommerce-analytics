CREATE OR REPLACE VIEW order_delivery AS
SELECT
    o.order_id,
    c.customer_state,
    o.order_delivered_customer_date::date - o.order_estimated_delivery_date::date AS delay_days,
    o.order_delivered_customer_date::date - o.order_purchase_timestamp::date AS delivery_days,
    r.review_score
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
JOIN (
    SELECT order_id, AVG(review_score) AS review_score
    FROM order_reviews
    GROUP BY order_id
) r ON o.order_id = r.order_id
WHERE o.order_status = 'delivered'
  AND o.order_delivered_customer_date IS NOT NULL;

SELECT
    CASE WHEN delay_days > 0 THEN 'Late' ELSE 'On time' END AS delivery_status,
    COUNT(*) AS orders,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS orders_pct,
    ROUND(AVG(review_score), 2) AS avg_review,
    ROUND(100.0 * COUNT(*) FILTER (WHERE review_score <= 2) / COUNT(*), 1) AS bad_review_pct
FROM order_delivery
GROUP BY 1
ORDER BY 1;

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
ORDER BY 1;

SELECT
    customer_state AS state,
    COUNT(*) AS orders,
    ROUND(AVG(delivery_days), 1) AS avg_delivery_days,
    ROUND(100.0 * COUNT(*) FILTER (WHERE delay_days > 0) / COUNT(*), 1) AS late_pct,
    ROUND(AVG(review_score), 2) AS avg_review
FROM order_delivery
GROUP BY 1
HAVING COUNT(*) >= 300
ORDER BY late_pct DESC
LIMIT 10;
