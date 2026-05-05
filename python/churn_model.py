"""
============================================================
Customer Churn Prediction & Retention Analysis
Machine Learning Pipeline
============================================================
Tools  : Python 3.x | Pandas | NumPy | Scikit-learn
Author : Portfolio Project
Output : Trained model + predictions CSV + evaluation report
============================================================
"""

import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings("ignore")

from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score, confusion_matrix,
    classification_report
)
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
import os

# ─────────────────────────────────────────────
# 1. LOAD DATA
# ─────────────────────────────────────────────
print("=" * 60)
print("  CUSTOMER CHURN PREDICTION — ML PIPELINE")
print("=" * 60)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "..", "data", "customer_churn.csv")

df = pd.read_csv(DATA_PATH)
print(f"\n[1] Data Loaded: {df.shape[0]:,} rows × {df.shape[1]} columns")
print(f"    Churn Rate  : {(df['Churn']=='Yes').mean()*100:.1f}%")

# ─────────────────────────────────────────────
# 2. DATA CLEANING & EXPLORATION
# ─────────────────────────────────────────────
print("\n[2] Data Quality Check")
print(f"    Missing values : {df.isnull().sum().sum()}")
print(f"    Duplicates     : {df.duplicated().sum()}")
print(f"    Data types     :\n{df.dtypes.value_counts().to_string()}")

# Drop internal risk columns (would leak target in production)
DROP_COLS = ["Customer_ID", "Churn_Probability", "Risk_Score", "Risk_Category"]
df_model = df.drop(columns=[c for c in DROP_COLS if c in df.columns])

# ─────────────────────────────────────────────
# 3. FEATURE ENGINEERING
# ─────────────────────────────────────────────
print("\n[3] Feature Engineering")

# Encode target
df_model["Churn_Binary"] = (df_model["Churn"] == "Yes").astype(int)
df_model.drop(columns=["Churn"], inplace=True)

# Binary flags
df_model["Has_Tech_Support"]    = (df_model["Tech_Support"] == "Yes").astype(int)
df_model["Has_Streaming"]       = (df_model["Streaming_Service"] == "Yes").astype(int)
df_model["Has_Security"]        = (df_model["Online_Security"] == "Yes").astype(int)
df_model["Is_Electronic_Check"] = (df_model["Payment_Method"] == "Electronic Check").astype(int)
df_model["Is_Month_to_Month"]   = (df_model["Contract_Type"] == "Month-to-Month").astype(int)
df_model["Is_Fiber"]            = (df_model["Internet_Service"] == "Fiber Optic").astype(int)

# Ratio features
df_model["Charge_per_Month_Tenure"] = np.where(
    df_model["Tenure"] > 0,
    df_model["Monthly_Charges"] / (df_model["Tenure"] + 1),
    df_model["Monthly_Charges"]
)
df_model["Total_vs_Expected"] = np.where(
    df_model["Tenure"] > 0,
    df_model["Total_Charges"] / (df_model["Monthly_Charges"] * (df_model["Tenure"] + 1)),
    1.0
)

# Age group
df_model["Age_Group"] = pd.cut(
    df_model["Age"],
    bins=[17, 25, 35, 45, 55, 65, 100],
    labels=[0, 1, 2, 3, 4, 5]
).astype(int)

# Drop original cols now encoded
df_model.drop(columns=["Tech_Support", "Streaming_Service", "Online_Security"], inplace=True)

# Encode remaining categoricals
cat_cols = df_model.select_dtypes(include="object").columns.tolist()
le = LabelEncoder()
for col in cat_cols:
    df_model[col] = le.fit_transform(df_model[col].astype(str))

print(f"    Final features : {df_model.shape[1] - 1}")
print(f"    Features list  : {list(df_model.columns[:-1])}")

# ─────────────────────────────────────────────
# 4. TRAIN / TEST SPLIT
# ─────────────────────────────────────────────
X = df_model.drop(columns=["Churn_Binary"])
y = df_model["Churn_Binary"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=42, stratify=y
)
print(f"\n[4] Train/Test Split")
print(f"    Train : {X_train.shape[0]:,} rows")
print(f"    Test  : {X_test.shape[0]:,} rows")
print(f"    Target distribution (train): {y_train.value_counts(normalize=True).to_dict()}")

# ─────────────────────────────────────────────
# 5. MODEL TRAINING
# ─────────────────────────────────────────────
print("\n[5] Model Training")

scaler = StandardScaler()
X_train_sc = scaler.fit_transform(X_train)
X_test_sc  = scaler.transform(X_test)

models = {
    "Logistic Regression": LogisticRegression(
        max_iter=500, C=1.0, random_state=42, class_weight="balanced"
    ),
    "Random Forest": RandomForestClassifier(
        n_estimators=150, max_depth=8, random_state=42, class_weight="balanced"
    ),
    "Gradient Boosting": GradientBoostingClassifier(
        n_estimators=100, learning_rate=0.1, max_depth=4, random_state=42
    ),
}

results = {}
for name, model in models.items():
    use_scaled = (name == "Logistic Regression")
    Xtr = X_train_sc if use_scaled else X_train
    Xte = X_test_sc  if use_scaled else X_test

    model.fit(Xtr, y_train)
    preds = model.predict(Xte)
    proba = model.predict_proba(Xte)[:, 1]

    cv = cross_val_score(model, Xtr, y_train, cv=StratifiedKFold(5), scoring="roc_auc")

    results[name] = {
        "model":     model,
        "accuracy":  accuracy_score(y_test, preds),
        "precision": precision_score(y_test, preds, zero_division=0),
        "recall":    recall_score(y_test, preds, zero_division=0),
        "f1":        f1_score(y_test, preds, zero_division=0),
        "roc_auc":   roc_auc_score(y_test, proba),
        "cv_auc":    cv.mean(),
        "cv_std":    cv.std(),
        "proba":     proba,
        "preds":     preds,
    }
    print(f"\n  ── {name} ──")
    print(f"     Accuracy  : {results[name]['accuracy']*100:.2f}%")
    print(f"     Precision : {results[name]['precision']*100:.2f}%")
    print(f"     Recall    : {results[name]['recall']*100:.2f}%")
    print(f"     F1 Score  : {results[name]['f1']*100:.2f}%")
    print(f"     ROC-AUC   : {results[name]['roc_auc']:.4f}")
    print(f"     CV AUC    : {results[name]['cv_auc']:.4f} ± {results[name]['cv_std']:.4f}")

# ─────────────────────────────────────────────
# 6. BEST MODEL SELECTION
# ─────────────────────────────────────────────
best_name = max(results, key=lambda n: results[n]["roc_auc"])
best      = results[best_name]
print(f"\n[6] Best Model: {best_name} (AUC = {best['roc_auc']:.4f})")
print("\n    Classification Report:")
print(classification_report(y_test, best["preds"], target_names=["Retained", "Churned"]))
print("    Confusion Matrix:")
cm = confusion_matrix(y_test, best["preds"])
print(f"    TN={cm[0,0]}  FP={cm[0,1]}")
print(f"    FN={cm[1,0]}  TP={cm[1,1]}")

# ─────────────────────────────────────────────
# 7. FEATURE IMPORTANCE (RANDOM FOREST)
# ─────────────────────────────────────────────
rf_model = results["Random Forest"]["model"]
importances = pd.Series(
    rf_model.feature_importances_, index=X.columns
).sort_values(ascending=False)

print("\n[7] Top 10 Feature Importances (Random Forest):")
for feat, imp in importances.head(10).items():
    bar = "█" * int(imp * 100)
    print(f"    {feat:<35} {bar} {imp:.4f}")

# ─────────────────────────────────────────────
# 8. GENERATE PREDICTIONS ON FULL DATASET
# ─────────────────────────────────────────────
print("\n[8] Generating Full-Dataset Predictions...")

# Re-encode full dataset
X_full = df_model.drop(columns=["Churn_Binary"])
y_full = df_model["Churn_Binary"]

rf_full_proba = rf_model.predict_proba(X_full)[:, 1]
rf_full_pred  = rf_model.predict(X_full)

lr_model      = results["Logistic Regression"]["model"]
X_full_sc     = scaler.transform(X_full)
lr_full_proba = lr_model.predict_proba(X_full_sc)[:, 1]

output_df = df[["Customer_ID", "Age", "Gender", "Tenure", "Contract_Type",
                 "Internet_Service", "Monthly_Charges", "Total_Charges",
                 "Satisfaction_Score", "Customer_Support_Calls", "Churn"]].copy()

output_df["RF_Churn_Probability"]  = (rf_full_proba * 100).round(2)
output_df["LR_Churn_Probability"]  = (lr_full_proba * 100).round(2)
output_df["Ensemble_Probability"]  = ((rf_full_proba + lr_full_proba) / 2 * 100).round(2)
output_df["Predicted_Churn"]       = np.where(rf_full_pred == 1, "Yes", "No")
output_df["Risk_Category"] = pd.cut(
    output_df["Ensemble_Probability"],
    bins=[0, 35, 60, 100],
    labels=["Low", "Medium", "High"]
)

OUTPUT_DIR = os.path.join(BASE_DIR, "..", "data")
os.makedirs(OUTPUT_DIR, exist_ok=True)
out_path = os.path.join(OUTPUT_DIR, "churn_predictions.csv")
output_df.to_csv(out_path, index=False)
print(f"    Saved: {out_path}")

# ─────────────────────────────────────────────
# 9. TOP 50 HIGH-RISK RETAINABLE CUSTOMERS
# ─────────────────────────────────────────────
print("\n[9] Top 50 High-Risk Retainable Customers:")
high_risk_retainable = (
    output_df[output_df["Churn"] == "No"]
    .sort_values("Ensemble_Probability", ascending=False)
    .head(50)
)
top50_path = os.path.join(OUTPUT_DIR, "top50_high_risk.csv")
high_risk_retainable.to_csv(top50_path, index=False)
print(f"    Saved: {top50_path}")
print(high_risk_retainable[["Customer_ID", "Ensemble_Probability",
                              "Risk_Category", "Monthly_Charges",
                              "Contract_Type"]].head(10).to_string(index=False))

# ─────────────────────────────────────────────
# 10. BUSINESS IMPACT SUMMARY
# ─────────────────────────────────────────────
print("\n[10] Business Impact Summary")
churned_customers   = output_df[output_df["Predicted_Churn"] == "Yes"]
monthly_rev_at_risk = churned_customers["Monthly_Charges"].sum()
annual_rev_at_risk  = monthly_rev_at_risk * 12
avg_churn_tenure    = churned_customers["Tenure"].mean()
high_risk_count     = (output_df["Risk_Category"] == "High").sum()

print(f"     Total Customers          : {len(output_df):,}")
print(f"     Predicted Churners       : {len(churned_customers):,}")
print(f"     Churn Rate               : {len(churned_customers)/len(output_df)*100:.1f}%")
print(f"     Monthly Revenue at Risk  : ${monthly_rev_at_risk:,.2f}")
print(f"     Annual Revenue at Risk   : ${annual_rev_at_risk:,.2f}")
print(f"     Avg Tenure (Churners)    : {avg_churn_tenure:.1f} months")
print(f"     High-Risk Active Customers: {high_risk_count:,}")
print(f"\n     Model Recommendation: Prioritize outreach to {len(high_risk_retainable)} high-risk")
print(f"     retainable customers — potential savings: ${high_risk_retainable['Monthly_Charges'].sum()*12:,.2f}/yr")

print("\n" + "=" * 60)
print("  PIPELINE COMPLETE — All outputs saved to /data/")
print("=" * 60)
