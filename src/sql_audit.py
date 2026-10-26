import pandas as pd
import sqlite3
import json

# ============================================================
# 1. LOAD AUDIT CONFIGURATION
# ============================================================

with open("config/audit_config.json", "r") as config_file:
    config = json.load(config_file)

HIGH_VALUE_THRESHOLD = config["high_value_threshold"]
ROUND_DOLLAR_BASE = config["round_dollar_base"]
RISK_WEIGHTS = config["risk_weights"]

# ============================================================
# 2. LOAD JOURNAL DATA
# ============================================================

journal = pd.read_csv("data/journal.csv")


# ============================================================
# 3. CREATE SQL DATABASE CONNECTION
# ============================================================

connection = sqlite3.connect("data/audit.db")


# Load the journal data into a SQL table.
journal.to_sql(
    "journal_entries",
    connection,
    if_exists="replace",
    index=False
)

print("Journal data loaded into SQL successfully.")

# ============================================================
# 4. RUN SQL AUDIT TESTS
# ============================================================

# Test 1: Identify high-value journal entries.
high_value_query = """
SELECT
    Journal_ID,
    Posting_Date,
    Account,
    Description,
    Amount,
    Prepared_By
FROM journal_entries
WHERE Amount >= ?
ORDER BY Amount DESC;
"""

high_value_results = pd.read_sql_query(
    high_value_query,
    connection,
    params=(HIGH_VALUE_THRESHOLD,)
)

print("\nHigh-Value Journal Entries:")
print(high_value_results)

# Test 2: Identify journal entries posted on weekends.
weekend_query = """
SELECT
    Journal_ID,
    Posting_Date,
    Account,
    Description,
    Amount,
    Prepared_By
FROM journal_entries
WHERE strftime('%w', Posting_Date) IN ('0', '6')
ORDER BY Posting_Date;
"""

weekend_results = pd.read_sql_query(
    weekend_query,
    connection
)

print("\nWeekend Journal Entries:")
print(weekend_results)

# Test 3: Identify potential duplicate journal entries.
duplicate_query = """
SELECT
    Posting_Date,
    Account,
    Description,
    Amount,
    Prepared_By,
    COUNT(*) AS Duplicate_Count
FROM journal_entries
GROUP BY
    Posting_Date,
    Account,
    Description,
    Amount,
    Prepared_By
HAVING COUNT(*) > 1
ORDER BY Duplicate_Count DESC;
"""

duplicate_results = pd.read_sql_query(
    duplicate_query,
    connection
)

print("\nPotential Duplicate Journal Entries:")
print(duplicate_results)

# Test 3B: Retrieve the individual transactions belonging
# to duplicate groups.
duplicate_detail_query = """
SELECT
    Journal_ID,
    Posting_Date,
    Account,
    Description,
    Amount,
    Prepared_By
FROM journal_entries
WHERE (
    Posting_Date,
    Account,
    Description,
    Amount,
    Prepared_By
) IN (
    SELECT
        Posting_Date,
        Account,
        Description,
        Amount,
        Prepared_By
    FROM journal_entries
    GROUP BY
        Posting_Date,
        Account,
        Description,
        Amount,
        Prepared_By
    HAVING COUNT(*) > 1
)
ORDER BY Posting_Date, Amount DESC;
"""

duplicate_detail_results = pd.read_sql_query(
    duplicate_detail_query,
    connection
)

print("\nDuplicate Transaction Details:")
print(duplicate_detail_results)

# Test 4: Identify round-dollar journal entries.
round_dollar_query = """
SELECT
    Journal_ID,
    Posting_Date,
    Account,
    Description,
    Amount,
    Prepared_By
FROM journal_entries
WHERE Amount = CAST(Amount AS INTEGER)
  AND CAST(Amount AS INTEGER) % ? = 0
ORDER BY Amount DESC;
"""

round_dollar_results = pd.read_sql_query(
    round_dollar_query,
    connection,
    params=(ROUND_DOLLAR_BASE,)
)

print("\nRound-Dollar Journal Entries:")
print(round_dollar_results)

# ============================================================
# SQL POPULATION SUMMARY
# ============================================================

summary_query = """
SELECT
    COUNT(*) AS Total_Entries,
    SUM(Amount) AS Total_Amount,
    AVG(Amount) AS Average_Amount,
    MIN(Amount) AS Minimum_Amount,
    MAX(Amount) AS Maximum_Amount
FROM journal_entries;
"""

summary_results = pd.read_sql_query(
    summary_query,
    connection
)

print("\nJournal Population Summary:")
print(summary_results)

# ============================================================
# ANALYZE JOURNAL ACTIVITY BY PREPARER
# ============================================================

preparer_query = """
SELECT
    Prepared_By,
    COUNT(*) AS Entry_Count,
    SUM(Amount) AS Total_Amount,
    AVG(Amount) AS Average_Amount,
    MAX(Amount) AS Maximum_Amount
FROM journal_entries
GROUP BY Prepared_By
ORDER BY Total_Amount DESC;
"""

preparer_results = pd.read_sql_query(
    preparer_query,
    connection
)

print("\nJournal Activity by Preparer:")
print(preparer_results)

# ============================================================
# ANALYZE HIGH-VALUE ACTIVITY BY PREPARER
# ============================================================

preparer_risk_query = """
SELECT
    Prepared_By,
    COUNT(*) AS Total_Entries,

    SUM(
        CASE
            WHEN Amount >= ? THEN 1
            ELSE 0
        END
    ) AS High_Value_Entries,

    SUM(Amount) AS Total_Amount

FROM journal_entries

GROUP BY Prepared_By

ORDER BY High_Value_Entries DESC, Total_Amount DESC;
"""

preparer_risk_results = pd.read_sql_query(
    preparer_risk_query,
    connection,
    params=(HIGH_VALUE_THRESHOLD,)
)

print("\nHigh-Value Activity by Preparer:")
print(preparer_risk_results)

# ============================================================
# CALCULATE TRANSACTION-LEVEL SQL RISK SCORES
# ============================================================

sql_risk_query = """
SELECT
    Journal_ID,
    Posting_Date,
    Account,
    Description,
    Amount,
    Prepared_By,

    CASE
        WHEN Amount >= ? THEN ?
        ELSE 0
    END
    +
    CASE
    WHEN Amount = CAST(Amount AS INTEGER)
         AND CAST(Amount AS INTEGER) % ? = 0
    THEN ?
    ELSE 0
    END
    +
CASE
    WHEN strftime('%w', Posting_Date) IN ('0', '6') THEN ?
    ELSE 0
END
+
CASE
    WHEN (
        Posting_Date,
        Account,
        Description,
        Amount,
        Prepared_By
    ) IN (
        SELECT
            Posting_Date,
            Account,
            Description,
            Amount,
            Prepared_By
        FROM journal_entries
        GROUP BY
            Posting_Date,
            Account,
            Description,
            Amount,
            Prepared_By
        HAVING COUNT(*) > 1
    )
    THEN ?
    ELSE 0
END
AS SQL_Risk_Score

FROM journal_entries

ORDER BY SQL_Risk_Score DESC;
"""
sql_risk_results = pd.read_sql_query(
    sql_risk_query,
    connection,
    params=(
        HIGH_VALUE_THRESHOLD,
        RISK_WEIGHTS["high_value"],
        ROUND_DOLLAR_BASE,
        RISK_WEIGHTS["round_dollar"],
        RISK_WEIGHTS["weekend_posting"],
        RISK_WEIGHTS["potential_duplicate"]
    )
)

print("\nSQL Transaction Risk Scores:")
print(sql_risk_results)

# ============================================================
# EXPORT SQL RISK RESULTS FOR RECONCILIATION
# ============================================================

sql_risk_results.to_csv(
    "output/sql_risk_results.csv",
    index=False
)

print("\nSQL risk results exported successfully.")

# Close the database connection.
connection.close()