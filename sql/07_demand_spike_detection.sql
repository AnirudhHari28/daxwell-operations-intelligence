-- Business question: Which products spiked in January 2025 volume vs. their own baseline?
WITH monthly_qty AS (
    SELECT product_id, DATE_TRUNC('month', date) AS month, SUM(quantity_sold) AS total_qty
    FROM fact_sales
    WHERE date IS NOT NULL
    GROUP BY product_id, DATE_TRUNC('month', date)
),
baseline AS (
    SELECT product_id, AVG(total_qty) AS avg_monthly_qty
    FROM monthly_qty
    WHERE month < DATE '2025-01-01'
    GROUP BY product_id
)
SELECT m.product_id, m.total_qty AS jan_2025_qty,
       ROUND(b.avg_monthly_qty, 0) AS normal_monthly_qty,
       ROUND(m.total_qty / b.avg_monthly_qty, 2) AS spike_ratio
FROM monthly_qty m
JOIN baseline b ON m.product_id = b.product_id
WHERE m.month = DATE '2025-01-01'
ORDER BY spike_ratio DESC;
