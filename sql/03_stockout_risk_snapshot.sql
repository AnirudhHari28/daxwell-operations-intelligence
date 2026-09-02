-- Business question: Which products are at risk of stockout as of the latest snapshot?
-- Caveat: a single day's snapshot can miss a product that JUST recovered --
-- see 04_stockout_risk_trend.sql for the more reliable version.
SELECT i.product_id, p.product_name, i.on_hand_qty, i.reorder_point,
       ROUND(i.on_hand_qty - i.reorder_point, 1) AS cushion
FROM fact_inventory_snapshot i
JOIN dim_products p ON i.product_id = p.product_id
WHERE i.snapshot_date = (SELECT MAX(snapshot_date) FROM fact_inventory_snapshot)
ORDER BY cushion ASC;
