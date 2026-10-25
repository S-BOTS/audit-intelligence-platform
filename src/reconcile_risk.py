import pandas as pd


# ============================================================
# 1. LOAD PYTHON AND SQL RESULTS
# ============================================================

python_results = pd.read_excel(
    "output/audit_risk_report.xlsx",
    sheet_name="Audit Results"
)

sql_results = pd.read_csv(
    "output/sql_risk_results.csv"
)


# ============================================================
# 2. COMBINE RESULTS BY JOURNAL ID
# ============================================================

reconciliation = python_results[
    ["Journal_ID", "Risk_Score"]
].merge(
    sql_results[
        ["Journal_ID", "SQL_Risk_Score"]
    ],
    on="Journal_ID",
    how="outer"
)


# ============================================================
# 3. COMPARE RISK SCORES
# ============================================================

reconciliation["Reconciliation_Status"] = (
    reconciliation["Risk_Score"]
    == reconciliation["SQL_Risk_Score"]
).map({
    True: "MATCH",
    False: "MISMATCH"
})


# ============================================================
# 4. DISPLAY RESULTS
# ============================================================

print("\nRisk Score Reconciliation:")
print(reconciliation)

mismatches = reconciliation[
    reconciliation["Reconciliation_Status"] == "MISMATCH"
]

print("\nTotal Mismatches:", len(mismatches))