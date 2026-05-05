-- ============================================================
-- CUSTOMER CHURN PREDICTION & RETENTION ANALYSIS
-- Advanced SQL Analytics Suite
-- Author: Portfolio Project | Tools: SQLite / PostgreSQL
-- ============================================================

-- ============================================================
-- QUERY 1: Overall Churn KPI Summary
-- ============================================================
SELECT
    COUNT(*)                                          AS total_customers,
    SUM(CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END)  AS churned_customers,
    ROUND(
        SUM(CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2
    )                                                 AS churn_rate_pct,
    ROUND(AVG(Monthly_Charges), 2)                   AS avg_monthly_charge,
    ROUND(SUM(CASE WHEN Churn = 'Yes' THEN Monthly_Charges ELSE 0 END), 2)
                                                      AS monthly_revenue_at_risk,
    ROUND(SUM(CASE WHEN Churn = 'Yes' THEN Monthly_Charges * 12 ELSE 0 END), 2)
                                                      AS annual_revenue_at_risk
FROM customer_churn;


-- ============================================================
-- QUERY 2: Churn Rate by Contract Type (Segmentation)
-- ============================================================
SELECT
    Contract_Type,
    COUNT(*)                                          AS total_customers,
    SUM(CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END)  AS churned,
    ROUND(
        SUM(CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2
    )                                                 AS churn_rate_pct,
    ROUND(AVG(Monthly_Charges), 2)                   AS avg_monthly_charges,
    ROUND(SUM(CASE WHEN Churn = 'Yes' THEN Monthly_Charges ELSE 0 END), 2)
                                                      AS revenue_at_risk
FROM customer_churn
GROUP BY Contract_Type
ORDER BY churn_rate_pct DESC;


-- ============================================================
-- QUERY 3: Revenue Loss Estimation by Internet Service
-- ============================================================
SELECT
    Internet_Service,
    COUNT(*)                                          AS customers,
    SUM(CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END)  AS churned,
    ROUND(AVG(Monthly_Charges), 2)                   AS avg_monthly,
    ROUND(
        SUM(CASE WHEN Churn = 'Yes' THEN Monthly_Charges ELSE 0 END), 2
    )                                                 AS monthly_loss,
    ROUND(
        SUM(CASE WHEN Churn = 'Yes' THEN Monthly_Charges * 12 ELSE 0 END), 2
    )                                                 AS projected_annual_loss,
    ROUND(
        SUM(CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2
    )                                                 AS churn_rate_pct
FROM customer_churn
GROUP BY Internet_Service
ORDER BY monthly_loss DESC;


-- ============================================================
-- QUERY 4: Age Group Churn Analysis
-- ============================================================
WITH age_segments AS (
    SELECT *,
        CASE
            WHEN Age BETWEEN 18 AND 25 THEN '18-25'
            WHEN Age BETWEEN 26 AND 35 THEN '26-35'
            WHEN Age BETWEEN 36 AND 45 THEN '36-45'
            WHEN Age BETWEEN 46 AND 55 THEN '46-55'
            WHEN Age BETWEEN 56 AND 65 THEN '56-65'
            ELSE '65+'
        END AS Age_Group
    FROM customer_churn
)
SELECT
    Age_Group,
    COUNT(*)                                             AS total_customers,
    SUM(CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END)     AS churned,
    ROUND(
        SUM(CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2
    )                                                    AS churn_rate_pct,
    ROUND(AVG(Satisfaction_Score), 2)                   AS avg_satisfaction,
    ROUND(AVG(Monthly_Charges), 2)                      AS avg_monthly_charges
FROM age_segments
GROUP BY Age_Group
ORDER BY Age_Group;


-- ============================================================
-- QUERY 5: Payment Method vs Churn (CTE + Ranking)
-- ============================================================
WITH payment_churn AS (
    SELECT
        Payment_Method,
        COUNT(*)                                              AS total,
        SUM(CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END)      AS churned,
        ROUND(
            SUM(CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2
        )                                                     AS churn_rate_pct,
        ROUND(AVG(Monthly_Charges), 2)                       AS avg_charge
    FROM customer_churn
    GROUP BY Payment_Method
)
SELECT
    *,
    RANK() OVER (ORDER BY churn_rate_pct DESC) AS churn_rank
FROM payment_churn
ORDER BY churn_rank;


-- ============================================================
-- QUERY 6: High-Risk Customer Identification (Top 50)
-- ============================================================
WITH risk_ranked AS (
    SELECT
        Customer_ID,
        Age,
        Gender,
        Contract_Type,
        Internet_Service,
        Monthly_Charges,
        Tenure,
        Customer_Support_Calls,
        Satisfaction_Score,
        Risk_Score,
        Risk_Category,
        Churn_Probability,
        ROW_NUMBER() OVER (ORDER BY Risk_Score DESC) AS risk_rank
    FROM customer_churn
    WHERE Churn = 'No'   -- Focus on retainable customers
)
SELECT *
FROM risk_ranked
WHERE risk_rank <= 50
ORDER BY Risk_Score DESC;


-- ============================================================
-- QUERY 7: Tenure Cohort Churn Analysis (Window Function)
-- ============================================================
WITH tenure_cohorts AS (
    SELECT *,
        CASE
            WHEN Tenure BETWEEN 0  AND 6  THEN '0-6 Months'
            WHEN Tenure BETWEEN 7  AND 12 THEN '7-12 Months'
            WHEN Tenure BETWEEN 13 AND 24 THEN '13-24 Months'
            WHEN Tenure BETWEEN 25 AND 48 THEN '25-48 Months'
            ELSE '49+ Months'
        END AS Tenure_Cohort
    FROM customer_churn
),
cohort_stats AS (
    SELECT
        Tenure_Cohort,
        COUNT(*)                                              AS total,
        SUM(CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END)      AS churned,
        ROUND(
            SUM(CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2
        )                                                     AS churn_pct,
        ROUND(AVG(Monthly_Charges), 2)                       AS avg_monthly,
        ROUND(SUM(CASE WHEN Churn = 'Yes' THEN Monthly_Charges ELSE 0 END), 2)
                                                              AS revenue_lost
    FROM tenure_cohorts
    GROUP BY Tenure_Cohort
)
SELECT
    *,
    ROUND(SUM(revenue_lost) OVER (ORDER BY Tenure_Cohort) , 2) AS cumulative_revenue_lost
FROM cohort_stats
ORDER BY Tenure_Cohort;


-- ============================================================
-- QUERY 8: Satisfaction Score Distribution vs Churn
-- ============================================================
SELECT
    ROUND(Satisfaction_Score) AS Satisfaction_Band,
    COUNT(*)                                              AS total_customers,
    SUM(CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END)      AS churned,
    ROUND(
        SUM(CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2
    )                                                     AS churn_rate_pct,
    ROUND(AVG(Monthly_Charges), 2)                       AS avg_monthly_charges
FROM customer_churn
GROUP BY ROUND(Satisfaction_Score)
ORDER BY Satisfaction_Band;


-- ============================================================
-- QUERY 9: Multi-Dimensional Churn Matrix (CTE + CASE)
-- ============================================================
WITH segment_matrix AS (
    SELECT *,
        CASE
            WHEN Contract_Type = 'Month-to-Month' AND Internet_Service = 'Fiber Optic'
                THEN 'High Risk Segment'
            WHEN Contract_Type = 'Month-to-Month' AND Internet_Service = 'DSL'
                THEN 'Moderate Risk Segment'
            WHEN Contract_Type IN ('One Year', 'Two Year')
                THEN 'Low Risk Segment'
            ELSE 'Other'
        END AS Customer_Segment
    FROM customer_churn
)
SELECT
    Customer_Segment,
    COUNT(*)                                              AS customers,
    SUM(CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END)      AS churned,
    ROUND(
        SUM(CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2
    )                                                     AS churn_pct,
    ROUND(AVG(Satisfaction_Score), 2)                    AS avg_satisfaction,
    ROUND(SUM(CASE WHEN Churn = 'Yes' THEN Monthly_Charges * 12 ELSE 0 END), 2)
                                                          AS annual_revenue_risk
FROM segment_matrix
GROUP BY Customer_Segment
ORDER BY churn_pct DESC;


-- ============================================================
-- QUERY 10: Customer Support Calls vs Churn (Binned)
-- ============================================================
SELECT
    Customer_Support_Calls,
    COUNT(*)                                              AS total,
    SUM(CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END)      AS churned,
    ROUND(
        SUM(CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2
    )                                                     AS churn_rate_pct,
    ROUND(AVG(Satisfaction_Score), 2)                    AS avg_satisfaction,
    ROUND(AVG(Monthly_Charges), 2)                       AS avg_monthly
FROM customer_churn
GROUP BY Customer_Support_Calls
ORDER BY Customer_Support_Calls;


-- ============================================================
-- QUERY 11: Monthly Revenue Run Rate & Churn Impact
-- ============================================================
WITH revenue_summary AS (
    SELECT
        Contract_Type,
        Gender,
        ROUND(SUM(Monthly_Charges), 2)                            AS total_mrr,
        ROUND(SUM(CASE WHEN Churn='Yes' THEN Monthly_Charges ELSE 0 END), 2)
                                                                   AS mrr_at_risk,
        ROUND(SUM(CASE WHEN Churn='No' THEN Monthly_Charges ELSE 0 END), 2)
                                                                   AS stable_mrr
    FROM customer_churn
    GROUP BY Contract_Type, Gender
)
SELECT
    *,
    ROUND(mrr_at_risk * 100.0 / total_mrr, 2)   AS pct_revenue_at_risk,
    ROUND(
        SUM(mrr_at_risk) OVER (PARTITION BY Contract_Type), 2
    )                                             AS contract_total_at_risk
FROM revenue_summary
ORDER BY pct_revenue_at_risk DESC;


-- ============================================================
-- QUERY 12: Add-on Services Impact on Retention
-- ============================================================
SELECT
    Tech_Support,
    Online_Security,
    Streaming_Service,
    COUNT(*)                                              AS customers,
    SUM(CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END)      AS churned,
    ROUND(
        SUM(CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2
    )                                                     AS churn_pct,
    ROUND(AVG(Monthly_Charges), 2)                       AS avg_monthly
FROM customer_churn
WHERE Internet_Service != 'No'
GROUP BY Tech_Support, Online_Security, Streaming_Service
ORDER BY churn_pct DESC
LIMIT 15;


-- ============================================================
-- QUERY 13: Running Churn Rate Trend by Tenure (Window)
-- ============================================================
WITH monthly_tenure AS (
    SELECT
        Tenure,
        COUNT(*)                                              AS cohort_size,
        SUM(CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END)      AS churned_count
    FROM customer_churn
    GROUP BY Tenure
)
SELECT
    Tenure,
    cohort_size,
    churned_count,
    ROUND(churned_count * 100.0 / cohort_size, 2)        AS period_churn_pct,
    SUM(churned_count) OVER (ORDER BY Tenure)            AS cumulative_churned,
    SUM(cohort_size)   OVER (ORDER BY Tenure)            AS cumulative_customers,
    ROUND(
        SUM(churned_count) OVER (ORDER BY Tenure) * 100.0 /
        SUM(cohort_size)   OVER (ORDER BY Tenure), 2
    )                                                     AS cumulative_churn_pct
FROM monthly_tenure
ORDER BY Tenure;


-- ============================================================
-- QUERY 14: Lifetime Value Estimation per Segment
-- ============================================================
WITH ltv_calc AS (
    SELECT *,
        CASE
            WHEN Contract_Type = 'Two Year'       THEN 24
            WHEN Contract_Type = 'One Year'        THEN 12
            ELSE 6
        END AS expected_months,
        Monthly_Charges * CASE
            WHEN Contract_Type = 'Two Year'       THEN 24
            WHEN Contract_Type = 'One Year'        THEN 12
            ELSE 6
        END AS estimated_ltv
    FROM customer_churn
)
SELECT
    Contract_Type,
    Internet_Service,
    COUNT(*)                                              AS customers,
    ROUND(AVG(estimated_ltv), 2)                         AS avg_ltv,
    ROUND(MIN(estimated_ltv), 2)                         AS min_ltv,
    ROUND(MAX(estimated_ltv), 2)                         AS max_ltv,
    ROUND(
        SUM(CASE WHEN Churn='Yes' THEN estimated_ltv ELSE 0 END), 2
    )                                                     AS ltv_lost_to_churn
FROM ltv_calc
GROUP BY Contract_Type, Internet_Service
ORDER BY avg_ltv DESC;


-- ============================================================
-- QUERY 15: Executive Churn Dashboard Summary (CTE Chain)
-- ============================================================
WITH base AS (
    SELECT
        COUNT(*)                                                 AS total_customers,
        SUM(CASE WHEN Churn='Yes' THEN 1 ELSE 0 END)           AS total_churned,
        ROUND(AVG(Monthly_Charges), 2)                          AS avg_monthly_charge,
        ROUND(SUM(Monthly_Charges), 2)                          AS total_mrr,
        ROUND(SUM(CASE WHEN Churn='Yes' THEN Monthly_Charges ELSE 0 END), 2)
                                                                 AS mrr_at_risk
    FROM customer_churn
),
high_risk AS (
    SELECT COUNT(*) AS high_risk_count
    FROM customer_churn
    WHERE Risk_Category = 'High' AND Churn = 'No'
),
top_contract AS (
    SELECT Contract_Type AS riskiest_contract
    FROM customer_churn
    GROUP BY Contract_Type
    ORDER BY SUM(CASE WHEN Churn='Yes' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) DESC
    LIMIT 1
)
SELECT
    b.total_customers,
    b.total_churned,
    ROUND(b.total_churned * 100.0 / b.total_customers, 2)  AS overall_churn_rate_pct,
    b.avg_monthly_charge,
    b.total_mrr,
    b.mrr_at_risk,
    ROUND(b.mrr_at_risk * 100.0 / b.total_mrr, 2)          AS pct_revenue_at_risk,
    ROUND(b.mrr_at_risk * 12, 2)                            AS projected_annual_loss,
    h.high_risk_count                                        AS retainable_high_risk,
    t.riskiest_contract
FROM base b, high_risk h, top_contract t;
