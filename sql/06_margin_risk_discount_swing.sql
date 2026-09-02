-- Business question: Which product's discounting has moved the most over time
-- (a proxy for undisclosed margin erosion)?
-- Caveat: products with very few sales rows (e.g. bad/orphaned IDs) can show
-- a noisy, misleading swing -- always sanity check row counts before trusting this.
WITH quarterly_discount AS (
    SELECT product_id, DATE_TRUNC('quarter', date) AS quarter,
           ROUND(AVG(discount_pct), 3) AS avg_discount
    FROM fact_sales
    WHERE date IS NOT NULL
    GROUP BY product_id, DATE_TRUNC('quarter', date)
)
SELECT product_id,
       ROUND(MAX(avg_discount) - MIN(avg_discount), 3) AS discount_swing
FROM quarterly_discount
GROUP BY product_id
ORDER BY discount_swing DESC;
