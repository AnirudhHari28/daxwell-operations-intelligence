-- Business question: Which customer segments have an above-average order value?
WITH segment_avg AS (
    SELECT c.segment,
           COUNT(*) AS num_orders,
           ROUND(SUM(s.revenue), 2) AS total_revenue,
           ROUND(AVG(s.revenue), 2) AS avg_order_value
    FROM fact_sales s
    JOIN dim_customers c ON s.customer_id = c.customer_id
    GROUP BY c.segment
)
SELECT *
FROM segment_avg
WHERE avg_order_value > (SELECT ROUND(AVG(revenue), 2) FROM fact_sales)
ORDER BY avg_order_value DESC;
