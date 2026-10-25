-- Signed invoice ledger bridge, not recognized accounting revenue.
-- Preserve every deduplicated line in the bridge, including exceptions.
CREATE OR REPLACE TABLE revenue_bridge AS
SELECT date_trunc('month',InvoiceDate)::DATE AS month,
 sum(CASE WHEN Quantity>0 AND UnitPrice>0 AND NOT upper(InvoiceNo) LIKE 'C%'
     THEN Quantity*UnitPrice ELSE 0 END) AS gross_purchase_sales,
 sum(CASE WHEN Quantity<0 AND UnitPrice>0 THEN -Quantity*UnitPrice ELSE 0 END) AS negative_quantity_value,
 sum(CASE WHEN NOT (Quantity>0 AND UnitPrice>0 AND NOT upper(InvoiceNo) LIKE 'C%')
          AND NOT (Quantity<0 AND UnitPrice>0) THEN Quantity*UnitPrice ELSE 0 END) AS exception_value,
 sum(Quantity*UnitPrice) AS signed_ledger_value
FROM ledger GROUP BY 1;
