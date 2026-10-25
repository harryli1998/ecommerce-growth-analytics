-- Purchase scope: positive quantity and price, non-cancellation, duplicates removed.
CREATE OR REPLACE TABLE orders AS
SELECT InvoiceNo AS order_id, CustomerID AS customer_id,
 min(InvoiceDate) AS ordered_at, min(Country) AS country,
 sum(Quantity * UnitPrice) AS revenue
FROM purchases GROUP BY 1,2;

CREATE OR REPLACE TABLE monthly AS
SELECT date_trunc('month',ordered_at)::DATE AS month,
 count(*) AS orders, sum(revenue) AS gross_sales,
 sum(revenue)/count(*) AS aov,
 count(distinct customer_id) AS identified_customers
FROM orders GROUP BY 1 ORDER BY 1;

-- First observed purchase is not necessarily lifetime acquisition.
CREATE OR REPLACE TABLE customers AS
SELECT customer_id, min(ordered_at) AS first_order,
 max(ordered_at) AS last_order, count(*) AS frequency,
 sum(revenue) AS monetary,
 date_diff('day',max(ordered_at),(SELECT max(InvoiceDate) FROM purchases)) AS recency_days
FROM orders WHERE customer_id IS NOT NULL GROUP BY 1;

-- Every denominator customer must have a complete 90-day observation window.
CREATE OR REPLACE TABLE repeat_90 AS
SELECT c.customer_id, c.first_order,
 max(CASE WHEN o.ordered_at > c.first_order
 AND o.ordered_at <= c.first_order + INTERVAL 90 DAY THEN 1 ELSE 0 END) AS repeated
FROM customers c JOIN orders o USING(customer_id)
WHERE c.first_order + INTERVAL 90 DAY < (SELECT max(InvoiceDate)::DATE FROM purchases)
GROUP BY 1,2;

CREATE OR REPLACE TABLE cohorts AS
WITH activity AS (
 SELECT distinct c.customer_id, date_trunc('month',c.first_order)::DATE AS cohort,
 date_diff('month',c.first_order,o.ordered_at) AS month_index
 FROM customers c JOIN orders o USING(customer_id)
 WHERE date_trunc('month',o.ordered_at) <
 (SELECT date_trunc('month',max(InvoiceDate)) FROM purchases)
), sizes AS (SELECT cohort,count(*) AS cohort_size FROM activity WHERE month_index=0 GROUP BY 1)
SELECT a.cohort,a.month_index,count(*) AS active_customers,s.cohort_size,
 count(*)::DOUBLE/s.cohort_size AS retention
FROM activity a JOIN sizes s USING(cohort) GROUP BY 1,2,4 ORDER BY 1,2;

CREATE OR REPLACE TABLE segments AS
SELECT *, CASE WHEN recency_days <= 90 AND frequency >= 3 THEN 'Active repeat'
 WHEN recency_days > 90 AND frequency >= 3 THEN 'Lapsed repeat'
 WHEN frequency = 1 THEN 'One-time observed' ELSE 'Occasional' END AS segment
FROM customers;

-- Fill observed zero-activity months; leave future cohort ages absent (NULL in chart).
CREATE OR REPLACE TABLE cohort_grid AS
SELECT c.cohort, i.month_index, coalesce(a.active_customers,0) AS active_customers,
 c.cohort_size, coalesce(a.active_customers,0)::DOUBLE/c.cohort_size AS retention
FROM (SELECT cohort,max(cohort_size) cohort_size FROM cohorts GROUP BY 1) c,
 LATERAL range(0,date_diff('month',c.cohort,
 (SELECT date_trunc('month',max(InvoiceDate)) FROM purchases))) i(month_index)
LEFT JOIN cohorts a ON a.cohort=c.cohort AND a.month_index=i.month_index;
CREATE OR REPLACE TABLE cohorts AS SELECT * FROM cohort_grid ORDER BY 1,2;
