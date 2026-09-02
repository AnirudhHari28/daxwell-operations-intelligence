-- Business question: Which products have been at risk over the last 30 days,
-- not just today? Catches products that recovered right before the snapshot.
SELECT product_id,
       SUM(CASE WHEN on_hand_qty <= reorder_point THEN 1 ELSE 0 END) AS days_below_reorder
FROM fact_inventory_snapshot
WHERE snapshot_date >= (SELECT MAX(snapshot_date) - INTERVAL 30 DAY FROM fact_inventory_snapshot)
GROUP BY product_id
ORDER BY days_below_reorder DESC;
