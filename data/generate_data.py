import pandas as pd
import numpy as np

np.random.seed(42)
N = 5500

customer_ids = [f"CUST-{str(i).zfill(5)}" for i in range(1, N+1)]
ages = np.clip(np.random.normal(42, 14, N).astype(int), 18, 80)
genders = np.random.choice(["Male", "Female"], N, p=[0.50, 0.50])
tenures = np.clip(np.random.exponential(24, N).astype(int), 0, 72)
contract_types = np.random.choice(
    ["Month-to-Month", "One Year", "Two Year"], N, p=[0.55, 0.25, 0.20])
payment_methods = np.random.choice(
    ["Electronic Check", "Mailed Check", "Bank Transfer", "Credit Card"], N,
    p=[0.34, 0.23, 0.22, 0.21])
internet_services = np.random.choice(
    ["Fiber Optic", "DSL", "No"], N, p=[0.44, 0.35, 0.21])
tech_supports = np.random.choice(["Yes", "No", "No Internet"], N, p=[0.29, 0.50, 0.21])
streaming_services = np.random.choice(["Yes", "No", "No Internet"], N, p=[0.38, 0.41, 0.21])
online_securities = np.random.choice(["Yes", "No", "No Internet"], N, p=[0.28, 0.51, 0.21])
support_calls = np.clip(np.random.poisson(2.5, N), 0, 10)
satisfaction_scores = np.clip(np.random.normal(3.2, 1.1, N), 1, 5).round(1)

base_monthly = np.where(internet_services == "Fiber Optic", 
                         np.random.normal(85, 15, N),
                         np.where(internet_services == "DSL",
                                  np.random.normal(55, 10, N),
                                  np.random.normal(25, 8, N)))
monthly_charges = np.clip(base_monthly, 18, 120).round(2)
total_charges = (monthly_charges * (tenures + 1) * np.random.uniform(0.90, 1.05, N)).round(2)

# Churn probability model
churn_score = (
    0.30 * (contract_types == "Month-to-Month").astype(float) +
    0.20 * (internet_services == "Fiber Optic").astype(float) +
    0.15 * (payment_methods == "Electronic Check").astype(float) +
    0.12 * (support_calls / 10) +
    0.10 * ((5 - satisfaction_scores) / 4) +
    0.08 * (tech_supports == "No").astype(float) +
    0.05 * (1 - tenures / 72)
)
churn_prob = 1 / (1 + np.exp(-5 * (churn_score - 0.45)))
churn_prob = np.clip(churn_prob + np.random.normal(0, 0.05, N), 0.02, 0.97)
churn = np.where(churn_prob > 0.50, "Yes", "No")

risk_score = (churn_prob * 100).round(1)
risk_label = np.where(risk_score >= 70, "High", np.where(risk_score >= 40, "Medium", "Low"))

month_map = {i: f"2024-{str(m).zfill(2)}" 
             for i, m in enumerate(np.random.choice(range(1,13), N))}
churn_month = np.where(churn == "Yes",
                        pd.array([f"2024-{str(np.random.randint(1,13)).zfill(2)}" for _ in range(N)]),
                        None)

df = pd.DataFrame({
    "Customer_ID": customer_ids,
    "Age": ages,
    "Gender": genders,
    "Tenure": tenures,
    "Contract_Type": contract_types,
    "Payment_Method": payment_methods,
    "Internet_Service": internet_services,
    "Tech_Support": tech_supports,
    "Streaming_Service": streaming_services,
    "Online_Security": online_securities,
    "Customer_Support_Calls": support_calls,
    "Satisfaction_Score": satisfaction_scores,
    "Monthly_Charges": monthly_charges,
    "Total_Charges": total_charges,
    "Churn_Probability": churn_prob.round(4),
    "Risk_Score": risk_score,
    "Risk_Category": risk_label,
    "Churn": churn
})

df.to_csv("/home/claude/churn-analysis/data/customer_churn.csv", index=False)
print(f"Dataset generated: {len(df)} rows")
print(f"Churn rate: {(df['Churn']=='Yes').mean()*100:.1f}%")
print(df.head(3))
