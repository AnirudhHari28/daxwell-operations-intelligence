-- Business question: What does the smoothed daily revenue trend look like,
-- filtering out day-to-day noise?
WITH daily_revenue AS (
    SELECT date, ROUND(SUM(revenue), 2) AS daily_revenue
    FROM fact_sales
    WHERE date IS NOT NULL
    GROUP BY date
)
SELECT date, daily_revenue,
       ROUND(AVG(daily_revenue) OVER (
           ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
       ), 2) AS rolling_7day_avg
FROM daily_revenue
ORDER BY date;
