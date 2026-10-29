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

# Derive individual Python audit-rule flags from Risk_Reasons
reasons = python_results["Risk_Reasons"].fillna("")

python_results["Python_Weekend_Posting"] = (
    reasons.str.contains("Weekend Posting", regex=False).astype(int)
)

python_results["Python_Round_Dollar"] = (
    reasons.str.contains("Round Dollar", regex=False).astype(int)
)

python_results["Python_High_Value"] = (
    reasons.str.contains("High Value", regex=False).astype(int)
)

python_results["Python_Potential_Duplicate"] = (
    reasons.str.contains("Potential Duplicate", regex=False).astype(int)
)

# ============================================================
# 2. COMBINE RESULTS BY JOURNAL ID
# ============================================================

reconciliation = python_results[
    [
        "Journal_ID",
        "Risk_Score",
        "Python_Weekend_Posting",
        "Python_Round_Dollar",
        "Python_High_Value",
        "Python_Potential_Duplicate"
    ]
].merge(
    sql_results[
        [
            "Journal_ID",
            "SQL_Risk_Score",
            "SQL_Weekend_Posting",
            "SQL_Round_Dollar",
            "SQL_High_Value",
            "SQL_Potential_Duplicate"
        ]
    ],
    on="Journal_ID",
    how="outer",
    validate="one_to_one"
)


# ============================================================
# 3. COMPARE RISK SCORES
# ============================================================

# 3. COMPARE PYTHON AND SQL AUDIT RESULTS

# Compare total risk scores
reconciliation["Risk_Score_Status"] = (
    reconciliation["Risk_Score"]
    == reconciliation["SQL_Risk_Score"]
).map({
    True: "MATCH",
    False: "MISMATCH"
})

# Compare weekend-posting flags
reconciliation["Weekend_Status"] = (
    reconciliation["Python_Weekend_Posting"]
    == reconciliation["SQL_Weekend_Posting"]
).map({
    True: "MATCH",
    False: "MISMATCH"
})

# Compare round-dollar flags
reconciliation["Round_Dollar_Status"] = (
    reconciliation["Python_Round_Dollar"]
    == reconciliation["SQL_Round_Dollar"]
).map({
    True: "MATCH",
    False: "MISMATCH"
})

# Compare high-value flags
reconciliation["High_Value_Status"] = (
    reconciliation["Python_High_Value"]
    == reconciliation["SQL_High_Value"]
).map({
    True: "MATCH",
    False: "MISMATCH"
})

# Compare potential-duplicate flags
reconciliation["Duplicate_Status"] = (
    reconciliation["Python_Potential_Duplicate"]
    == reconciliation["SQL_Potential_Duplicate"]
).map({
    True: "MATCH",
    False: "MISMATCH"
})

# Overall reconciliation passes only when every comparison matches
status_columns = [
    "Risk_Score_Status",
    "Weekend_Status",
    "Round_Dollar_Status",
    "High_Value_Status",
    "Duplicate_Status"
]

reconciliation["Reconciliation_Status"] = (
    reconciliation[status_columns]
    .eq("MATCH")
    .all(axis=1)
    .map({
        True: "MATCH",
        False: "MISMATCH"
    })
)


# ============================================================
# 4. DISPLAY RESULTS
# ============================================================

print("\nRisk Score Reconciliation:")
print(reconciliation)

mismatches = reconciliation[
    reconciliation["Reconciliation_Status"] == "MISMATCH"
]

print("\nTotal Mismatches:", len(mismatches))