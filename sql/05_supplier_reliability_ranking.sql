-- Business question: Which suppliers are the least reliable on delivery timing?
WITH delays AS (
    SELECT supplier_id,
           DATE_DIFF('day', expected_delivery_date, actual_delivery_date) AS delay_days
    FROM fact_purchase_orders
    WHERE status = 'Delivered'
),
supplier_avg_delay AS (
    SELECT supplier_id, ROUND(AVG(delay_days), 1) AS avg_delay_days
    FROM delays
    GROUP BY supplier_id
)
SELECT supplier_id, avg_delay_days,
       RANK() OVER (ORDER BY avg_delay_days DESC) AS delay_rank
FROM supplier_avg_delay
ORDER BY delay_rank;
