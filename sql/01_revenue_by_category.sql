-- Business question: Which product category drives the most revenue?
SELECT p.category,
       ROUND(SUM(s.revenue), 2) AS total_revenue,
       SUM(s.quantity_sold) AS total_units
FROM fact_sales s
JOIN dim_products p ON s.product_id = p.product_id
GROUP BY p.category
ORDER BY total_revenue DESC;
