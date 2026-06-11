select * from olist.public.customers
limit 10 ;


-- Completing the name of the Brazil States
select distinct customers.customer_state from customers;

UPDATE olist.public.customers
SET customer_state = CASE customer_state
    WHEN 'AC' THEN 'Acre'
    WHEN 'AL' THEN 'Alagoas'
    WHEN 'AM' THEN 'Amazonas'
    WHEN 'AP' THEN 'Amapá'
    WHEN 'BA' THEN 'Bahia'
    WHEN 'CE' THEN 'Ceará'
    WHEN 'DF' THEN 'Distrito Federal'
    WHEN 'ES' THEN 'Espírito Santo'
    WHEN 'GO' THEN 'Goiás'
    WHEN 'MA' THEN 'Maranhão'
    WHEN 'MG' THEN 'Minas Gerais'
    WHEN 'MS' THEN 'Mato Grosso do Sul'
    WHEN 'MT' THEN 'Mato Grosso'
    WHEN 'PA' THEN 'Pará'
    WHEN 'PB' THEN 'Paraíba'
    WHEN 'PE' THEN 'Pernambuco'
    WHEN 'PI' THEN 'Piauí'
    WHEN 'PR' THEN 'Paraná'
    WHEN 'RJ' THEN 'Rio de Janeiro'
    WHEN 'RN' THEN 'Rio Grande do Norte'
    WHEN 'RO' THEN 'Rondônia'
    WHEN 'RR' THEN 'Roraima'
    WHEN 'RS' THEN 'Rio Grande do Sul'
    WHEN 'SC' THEN 'Santa Catarina'
    WHEN 'SE' THEN 'Sergipe'
    WHEN 'SP' THEN 'São Paulo'
    WHEN 'TO' THEN 'Tocantins'
    ELSE customer_state
END
where customer_state is not null;

-- 1. Top 3 states with most sales (by order count)
SELECT c.customer_state,
       COUNT(DISTINCT o.order_id) AS total_orders
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_state
ORDER BY total_orders DESC
LIMIT 3;

-- 2. Top 3 most profitable states (by total revenue)
SELECT c.customer_state,
       ROUND(SUM(oi.price)::numeric, 2) AS total_revenue
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
JOIN order_items oi ON o.order_id = oi.order_id
GROUP BY c.customer_state
ORDER BY total_revenue DESC
LIMIT 3;

-- 3. Top 3 states with top 3 product categories
WITH state_category_revenue AS (
    SELECT c.customer_state,
           COALESCE(pct.product_category_name_english, p.product_category_name) AS category,
           ROUND(SUM(oi.price)::numeric, 2) AS revenue,
           ROW_NUMBER() OVER (
               PARTITION BY c.customer_state
               ORDER BY SUM(oi.price) DESC
           ) AS rn
    FROM customers c
    JOIN orders o ON c.customer_id = o.customer_id
    JOIN order_items oi ON o.order_id = oi.order_id
    JOIN products p ON oi.product_id = p.product_id
    LEFT JOIN product_category_translation pct ON p.product_category_name = pct.product_category_name
    GROUP BY c.customer_state, category
),
top_states AS (
    SELECT customer_state
    FROM state_category_revenue
    WHERE rn = 1
    ORDER BY revenue DESC
    LIMIT 3
)
SELECT ts.customer_state,
       scr.category,
       scr.revenue,
       scr.rn AS category_rank
FROM top_states ts
JOIN state_category_revenue scr ON ts.customer_state = scr.customer_state
WHERE scr.rn <= 3
ORDER BY ts.customer_state, scr.rn;

-- 4. Customers added per month and year (based on first order date)
WITH valid_orders AS (
    SELECT *
    FROM orders
    WHERE order_purchase_timestamp IS NOT NULL
      AND order_purchase_timestamp != ''
),
first_purchase AS (
    SELECT c.customer_unique_id,
           MIN((o.order_purchase_timestamp)::timestamp) AS first_order_date
    FROM customers c
    JOIN valid_orders o ON c.customer_id = o.customer_id
    GROUP BY c.customer_unique_id
)
SELECT EXTRACT(YEAR FROM first_order_date) AS year,
       EXTRACT(MONTH FROM first_order_date) AS month,
       COUNT(*) AS new_customers
FROM first_purchase
GROUP BY year, month
ORDER BY year, month;

-- 5. Most profitable month in each year
WITH valid_orders AS (
    SELECT *
    FROM orders
    WHERE order_purchase_timestamp IS NOT NULL
      AND order_purchase_timestamp != ''
),
monthly_revenue AS (
    SELECT EXTRACT(YEAR FROM (o.order_purchase_timestamp)::timestamp) AS year,
           EXTRACT(MONTH FROM (o.order_purchase_timestamp)::timestamp) AS month,
           ROUND(SUM(oi.price)::numeric, 2) AS revenue
    FROM valid_orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    GROUP BY year, month
),
ranked_months AS (
    SELECT *,
           ROW_NUMBER() OVER (PARTITION BY year ORDER BY revenue DESC) AS rn
    FROM monthly_revenue
)
SELECT year, month, revenue
FROM ranked_months
WHERE rn = 1
ORDER BY year;

-- =====================
-- Customer Metrics
-- =====================

-- 0. Helper: years where data exists
DROP VIEW IF EXISTS all_years;
CREATE TEMP VIEW all_years AS
WITH valid_orders AS (
    SELECT *
    FROM orders
    WHERE order_purchase_timestamp IS NOT NULL AND order_purchase_timestamp != ''
      AND order_status NOT IN ('canceled', 'unavailable')
)
SELECT DISTINCT EXTRACT(YEAR FROM (order_purchase_timestamp)::timestamp)::int AS year
FROM valid_orders;

-- 1. Customer Retention Rate (CRR) by year
-- CRR = (Customers active in Y who also ordered in Y+1 / Customers active in Y) * 100
WITH valid_orders AS (
    SELECT o.*, c.customer_unique_id
    FROM orders o
    JOIN customers c ON o.customer_id = c.customer_id
    WHERE o.order_purchase_timestamp IS NOT NULL AND o.order_purchase_timestamp != ''
      AND o.order_status NOT IN ('canceled', 'unavailable')
),
yearly_active AS (
    SELECT DISTINCT customer_unique_id,
           EXTRACT(YEAR FROM (order_purchase_timestamp)::timestamp)::int AS year
    FROM valid_orders
)
SELECT a.year AS start_year,
       COUNT(DISTINCT a.customer_unique_id) AS active_customers,
       COUNT(DISTINCT b.customer_unique_id) AS retained_next_year,
       ROUND(
           (COUNT(DISTINCT b.customer_unique_id)::numeric
            / NULLIF(COUNT(DISTINCT a.customer_unique_id), 0)) * 100, 2
       ) AS crr_pct
FROM yearly_active a
LEFT JOIN yearly_active b
    ON a.customer_unique_id = b.customer_unique_id
   AND b.year = a.year + 1
GROUP BY a.year
ORDER BY a.year;

-- 2. Repeat Purchase Rate (RPR)
-- Customers with >1 purchase / Total customers * 100
WITH customer_order_count AS (
    SELECT c.customer_unique_id,
           COUNT(DISTINCT o.order_id) AS order_count
    FROM customers c
    JOIN orders o ON c.customer_id = o.customer_id
    GROUP BY c.customer_unique_id
)
SELECT COUNT(*) FILTER (WHERE order_count > 1) AS repeat_customers,
       COUNT(*) AS total_customers,
       ROUND((COUNT(*) FILTER (WHERE order_count > 1)::numeric / COUNT(*)) * 100, 2) AS repeat_purchase_rate
FROM customer_order_count;

-- 3. Customer Churn Rate by year
-- Customers whose last order was in year Y (and data has a later year) / Customers active in Y * 100
WITH valid_orders AS (
    SELECT o.*, c.customer_unique_id
    FROM orders o
    JOIN customers c ON o.customer_id = c.customer_id
    WHERE o.order_purchase_timestamp IS NOT NULL AND o.order_purchase_timestamp != ''
      AND o.order_status NOT IN ('canceled', 'unavailable')
),
customer_year_range AS (
    SELECT customer_unique_id,
           MIN(EXTRACT(YEAR FROM (order_purchase_timestamp)::timestamp)::int) AS first_year,
           MAX(EXTRACT(YEAR FROM (order_purchase_timestamp)::timestamp)::int) AS last_year
    FROM valid_orders
    GROUP BY customer_unique_id
),
max_year AS (
    SELECT MAX(last_year) AS yr FROM customer_year_range
)
SELECT cyr.last_year AS year,
       COUNT(*) AS customers_at_start,
       COUNT(*) FILTER (WHERE cyr.last_year < my.yr) AS churned,
       ROUND(
           (COUNT(*) FILTER (WHERE cyr.last_year < my.yr)::numeric
            / NULLIF(COUNT(*), 0)) * 100, 2
       ) AS churn_rate
FROM customer_year_range cyr
CROSS JOIN max_year my
GROUP BY cyr.last_year, my.yr
ORDER BY cyr.last_year;

-- 4. Customer Lifetime Value (LTV)
WITH customer_value AS (
    SELECT c.customer_unique_id,
           COUNT(DISTINCT o.order_id) AS total_orders,
           ROUND(SUM(oi.price)::numeric, 2) AS total_revenue,
           EXTRACT(YEAR FROM AGE(
               MAX((o.order_purchase_timestamp)::timestamp),
               MIN((o.order_purchase_timestamp)::timestamp)
           )) + 1 AS lifespan_years
    FROM customers c
    JOIN orders o ON c.customer_id = o.customer_id
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE o.order_purchase_timestamp IS NOT NULL AND o.order_purchase_timestamp != ''
      AND o.order_status NOT IN ('canceled', 'unavailable')
    GROUP BY c.customer_unique_id
)
SELECT ROUND(AVG(total_revenue / NULLIF(total_orders, 0)), 2) AS avg_order_value,
       ROUND(AVG(total_orders), 2) AS avg_purchases_per_customer,
       ROUND(AVG(lifespan_years), 2) AS avg_lifespan_years,
       ROUND(AVG(total_revenue), 2) AS avg_ltv_per_customer
FROM customer_value;

-- 5. Customer Satisfaction Score (CSAT)
-- Positive scores (4-5) / Total responses * 100
SELECT COUNT(*) AS total_reviews,
       COUNT(*) FILTER (WHERE review_score >= 4) AS positive_scores,
       ROUND((COUNT(*) FILTER (WHERE review_score >= 4)::numeric / COUNT(*)) * 100, 2) AS csat_pct
FROM order_reviews;

-- 6. Net Promoter Score (NPS)
-- % Promoters (9-10) - % Detractors (1-6)
WITH score_groups AS (
    SELECT COUNT(*) FILTER (WHERE review_score IN (9, 10)) AS promoters,
           COUNT(*) FILTER (WHERE review_score BETWEEN 1 AND 6) AS detractors,
           COUNT(*) FILTER (WHERE review_score IN (7, 8)) AS passives,
           COUNT(*) AS total
    FROM order_reviews
)
SELECT promoters,
       detractors,
       passives,
       ROUND((promoters::numeric / total) * 100, 2) AS promoters_pct,
       ROUND((detractors::numeric / total) * 100, 2) AS detractors_pct,
       ROUND(((promoters::numeric - detractors::numeric) / total) * 100, 2) AS nps
FROM score_groups;

-- 7. Customer Effort Score (CES)
SELECT ROUND(AVG(review_score), 2) AS avg_review_score,
       ROUND(STDDEV(review_score), 2) AS stddev_review_score
FROM order_reviews;
