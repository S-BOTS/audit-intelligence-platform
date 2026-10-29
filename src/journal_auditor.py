import pandas as pd
import json
from openpyxl.styles import Font,PatternFill
from openpyxl.chart import BarChart, Reference
import sqlite3
import hashlib
from datetime import datetime

# Create timestamp for this audit run
run_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Create a fingerprint of the journal data and audit configuration.
# The fingerprint proves which inputs were used for this audit run.
hasher = hashlib.sha256()

with open("data/journal.csv", "rb") as file:
    hasher.update(file.read())

with open("config/audit_config.json", "rb") as file:
    hasher.update(file.read())

input_fingerprint = hasher.hexdigest()
# ============================================================
# 1. LOAD AUDIT CONFIGURATION
# ============================================================
# Audit thresholds, risk weights, and risk-level definitions
# are stored separately in JSON so they can be changed without
# modifying the core Python audit logic.

with open("config/audit_config.json", "r") as config_file:
    config = json.load(config_file)

# Extract configuration settings
ROUND_DOLLAR_BASE = config["round_dollar_base"]
HIGH_VALUE_THRESHOLD = config["high_value_threshold"]

RISK_WEIGHTS = config["risk_weights"]
RISK_LEVELS = config["risk_levels"]

# ============================================================
# 2. VALIDATE AUDIT CONFIGURATION
# ============================================================

# Thresholds used in calculations must be greater than zero.
if ROUND_DOLLAR_BASE <= 0:
    raise ValueError(
        "Configuration error: round_dollar_base must be greater than 0."
    )

if HIGH_VALUE_THRESHOLD <= 0:
    raise ValueError(
        "Configuration error: high_value_threshold must be greater than 0."
    )

# Risk weights cannot be negative.
for risk_name, weight in RISK_WEIGHTS.items():
    if weight < 0:
        raise ValueError(
            f"Configuration error: risk weight '{risk_name}' "
            f"cannot be negative."
        )

# Risk-level thresholds must follow a logical order.
if RISK_LEVELS["medium"] >= RISK_LEVELS["high"]:
    raise ValueError(
        "Configuration error: medium risk threshold "
        "must be lower than high risk threshold."
    )

# ============================================================
# 3. LOAD AND PREPARE JOURNAL DATA
# ============================================================

# Load journal entries from CSV
journal = pd.read_csv("data/journal.csv")

# ============================================================
# 4. VALIDATE JOURNAL DATA
# ============================================================

# Define the minimum fields required by the audit tests.
REQUIRED_COLUMNS = [
    "Journal_ID",
    "Posting_Date",
    "Account",
    "Description",
    "Amount",
    "Prepared_By"
]

# Identify any required columns missing from the input file.
missing_columns = [
    column for column in REQUIRED_COLUMNS
    if column not in journal.columns
]

# Stop processing if required audit data is unavailable.
if missing_columns:
    raise ValueError(
        f"Audit cannot continue. Missing required columns: {missing_columns}"
    )

# Check required fields for missing/null values.
missing_values = journal[REQUIRED_COLUMNS].isnull().sum()

# Keep only fields that actually contain missing values.
missing_values = missing_values[missing_values > 0]

if not missing_values.empty:
    raise ValueError(
        f"Audit cannot continue. Missing values found:\n{missing_values}"
    )

# Convert Posting_Date to datetime.
# Invalid dates are converted to NaT (Not a Time) instead of crashing.
journal["Posting_Date"] = pd.to_datetime(
    journal["Posting_Date"],
    errors="coerce"
)

# Identify records containing invalid dates.
invalid_dates = journal[journal["Posting_Date"].isnull()]

if not invalid_dates.empty:
    raise ValueError(
        f"Audit cannot continue. Invalid Posting_Date values found "
        f"in {len(invalid_dates)} record(s)."
    )

# Convert Amount to numeric.
# Invalid values are converted to NaN instead of crashing.
journal["Amount"] = pd.to_numeric(
    journal["Amount"],
    errors="coerce"
)

# Identify records containing invalid amounts.
invalid_amounts = journal[journal["Amount"].isnull()]

if not invalid_amounts.empty:
    raise ValueError(
        f"Audit cannot continue. Invalid Amount values found "
        f"in {len(invalid_amounts)} record(s)."
    )

# Display basic information about the journal dataset
print(journal.head())
print("Total journal entries:", len(journal))
print("\n Journal Fields:" )
print(journal.columns)
print("\n Journal Data Types:")
print(journal.dtypes)
# ============================================================
# 5. IDENTIFY AUDIT EXCEPTIONS
# ============================================================

# Test 1: Identify journal entries posted on Saturday or Sunday
weekend_entries = journal[journal["Posting_Date"].dt.weekday >= 5]
print("\n Weekend Journal Entries:")
print(weekend_entries)
# Test 2: Identify potential duplicate journal entries
# Entries are considered duplicates when these key fields match.
duplicate_entries = journal[journal.duplicated(subset=["Posting_Date","Account","Description","Amount","Prepared_By"], keep=False)]
print("\n Duplicate Journal Entries:")
print(duplicate_entries)
# Test 3: Identify transactions divisible by the configured
# round-dollar base (for example, $1,000, $5,000, $10,000).
round_entries = journal[journal["Amount"] % ROUND_DOLLAR_BASE == 0]
print("\n Round-DollarJournal Entries:")
print(round_entries)
# Test 4: Identify transactions meeting or exceeding the
# configured high-value threshold.  
high_value_entries = journal[journal["Amount"] >= HIGH_VALUE_THRESHOLD]
print("\n High-Value Journal Entries:")
print(high_value_entries)
# ============================================================
# 6. CALCULATE AUDIT RISK SCORES
# ============================================================

# Every journal entry starts with a risk score of zero.
journal["Risk_Score"] = 0 
# Risk_Reasons provides an audit trail explaining why each
# transaction received its risk score.
journal["Risk_Reasons"] = ""
# Apply audit risk tests
# Weekend posting risk
journal.loc[journal["Posting_Date"].dt.weekday >= 5, "Risk_Score"] += RISK_WEIGHTS["weekend_posting"]
journal.loc[journal["Posting_Date"].dt.weekday >= 5, "Risk_Reasons"] += "Weekend Posting; "
# Round-dollar transaction risk
journal.loc[journal["Amount"] % ROUND_DOLLAR_BASE == 0, "Risk_Score"] += RISK_WEIGHTS["round_dollar"]
journal.loc[journal["Amount"] % ROUND_DOLLAR_BASE == 0, "Risk_Reasons"] += "Round Dollar; "
# High-value transaction risk
journal.loc[journal["Amount"] >= HIGH_VALUE_THRESHOLD, "Risk_Score"] += RISK_WEIGHTS["high_value"]
journal.loc[journal["Amount"] >= HIGH_VALUE_THRESHOLD, "Risk_Reasons"] += "High Value; "
# Potential duplicate transaction risk
journal.loc[duplicate_entries.index, "Risk_Score"] += RISK_WEIGHTS["potential_duplicate"]
journal.loc[duplicate_entries.index, "Risk_Reasons"] += "Potential Duplicate; "
# ============================================================
# 7. CLASSIFY TRANSACTIONS BY RISK LEVEL
# ============================================================

# All transactions start as Low risk. Transactions are then
# upgraded to Medium or High based on configured score thresholds.
journal["Risk_Level"] = "Low"

journal.loc[
    journal["Risk_Score"] >= RISK_LEVELS["medium"],
    "Risk_Level"
] = "Medium"

journal.loc[
    journal["Risk_Score"] >= RISK_LEVELS["high"],
    "Risk_Level"
] = "High"
# ============================================================
# 8. CREATE AUDIT SUMMARY
# ============================================================

# Calculate population-level audit statistics.
total_entries = len(journal)

high_risk_count = (journal["Risk_Level"] == "High").sum()
medium_risk_count = (journal["Risk_Level"] == "Medium").sum()
low_risk_count = (journal["Risk_Level"] == "Low").sum()

flagged_entries = (journal["Risk_Score"] > 0).sum()

# Calculate the percentage of the population containing
# at least one configured risk indicator.
flagged_percentage = (
    flagged_entries / total_entries * 100
    if total_entries > 0
    else 0
)

print("\n======================================")
print("AUDIT ANALYTICS SUMMARY")
print("======================================")
print(f"Total Journal Entries : {total_entries}")
print(f"Flagged Entries       : {flagged_entries}")
print(f"Flagged Percentage    : {flagged_percentage:.2f}%")
print(f"High Risk             : {high_risk_count}")
print(f"Medium Risk           : {medium_risk_count}")
print(f"Low Risk              : {low_risk_count}")

# Create a summary table for the Excel audit report.
audit_summary = pd.DataFrame({
    "Metric": [
        "Run Timestamp",
        "Input Fingerprint",
        "Total Journal Entries",
        "Flagged Entries",
        "Flagged Percentage",
        "High Risk",
        "Medium Risk",
        "Low Risk"
    ],
    "Value": [
        run_timestamp,
        input_fingerprint,
        total_entries,
        flagged_entries,
        f"{flagged_percentage:.2f}%",
        high_risk_count,
        medium_risk_count,
        low_risk_count
    ]
})

# ============================================================
# 9. PRIORITIZE AND EXPORT AUDIT RESULTS
# ============================================================

# Sort highest-risk transactions first so auditors can focus
# their review on entries with the greatest number/weight of
# configured risk indicators.
risk_report = journal.sort_values(by="Risk_Score", ascending=False)
# Display prioritized results
print("\nPrioritized Audit Risk Report:")
print(risk_report[["Journal_ID","Posting_Date","Amount","Prepared_By","Risk_Score","Risk_Level","Risk_Reasons"]])
# Export the complete analyzed journal population to Excel.
# OLD EXPORT - replaced by multi-sheet audit report
# risk_report.to_excel("output/audit_risk_report.xlsx", index=False)
# Export audit results and summary into separate Excel worksheets.
with pd.ExcelWriter(
    "output/audit_risk_report.xlsx",
    engine="openpyxl"
) as writer:

    risk_report.to_excel(
        writer,
        sheet_name="Audit Results",
        index=False
    )

    audit_summary.to_excel(
        writer,
        sheet_name="Audit Summary",
        index=False
    )
    # Access the generated Audit Results worksheet.
    results_sheet = writer.sheets["Audit Results"]

    # Make the header row bold.
    for cell in results_sheet[1]:
        cell.font = Font(bold=True)

    # Freeze the header while scrolling.
    results_sheet.freeze_panes = "A2"

    # Add Excel filters to the complete results table.
    results_sheet.auto_filter.ref = results_sheet.dimensions
        # Automatically adjust column widths based on content.
    for column in results_sheet.columns:
        max_length = 0
        column_letter = column[0].column_letter

        for cell in column:
            if cell.value is not None:
                max_length = max(max_length, len(str(cell.value)))

        results_sheet.column_dimensions[column_letter].width = max_length + 2
        
        # Format the Amount column as currency.
    amount_column = risk_report.columns.get_loc("Amount") + 1

    for cell in results_sheet.iter_cols(
        min_col=amount_column,
        max_col=amount_column,
        min_row=2
    ):
        for amount_cell in cell:
            amount_cell.number_format = '$#,##0.00'

        # Add extra space to the Amount column for currency formatting.
        amount_letter = results_sheet.cell(
        row=1,
        column=amount_column
    ).column_letter

    results_sheet.column_dimensions[amount_letter].width += 3

        # Visually highlight transaction risk levels.
    risk_level_column = risk_report.columns.get_loc("Risk_Level") + 1

    high_fill = PatternFill("solid", fgColor="F4CCCC")
    medium_fill = PatternFill("solid", fgColor="FFF2CC")
    low_fill = PatternFill("solid", fgColor="D9EAD3")

    for row in range(2, results_sheet.max_row + 1):
        cell = results_sheet.cell(row=row, column=risk_level_column)

        if cell.value == "High":
            cell.fill = high_fill
        elif cell.value == "Medium":
            cell.fill = medium_fill
        elif cell.value == "Low":
            cell.fill = low_fill

        # Access the Audit Summary worksheet.
        summary_sheet = writer.sheets["Audit Summary"]

    # Make summary headers bold.
    for cell in summary_sheet[1]:
        cell.font = Font(bold=True)

    # Automatically adjust summary column widths.
    for column in summary_sheet.columns:
        max_length = 0
        column_letter = column[0].column_letter

        for cell in column:
            if cell.value is not None:
                max_length = max(max_length, len(str(cell.value)))

        summary_sheet.column_dimensions[column_letter].width = max_length + 3

            # Create a chart showing the distribution of audit risk levels.
        chart = BarChart()
        chart.title = "Risk Distribution"
        chart.y_axis.title = "Number of Journal Entries"
        chart.x_axis.title = "Risk Level"

    # Values: High, Medium and Low counts in rows 5–7.
    data = Reference(
        summary_sheet,
        min_col=2,
        min_row=5,
        max_row=7
    )

    # Categories: High Risk, Medium Risk and Low Risk.
    categories = Reference(
        summary_sheet,
        min_col=1,
        min_row=5,
        max_row=7
    )

    chart.add_data(data, titles_from_data=False)
    chart.set_categories(categories)

    # Place the chart beside the summary.
    summary_sheet.add_chart(chart, "D2")

print("\nAudit risk report exported successfully.")    


# ============================================================
# GIT / GITHUB CHEAT SHEET — DO NOT RUN AS PYTHON
# ============================================================

# 1. Check what files have changed
# git status

# 2. Stage all changes for the next commit
# git add .

# 3. Create a commit with a description of what changed
# git commit -m "Add configuration and data validation"

# 4. Upload the commit to GitHub
# git push

# Useful commands:
# git log --oneline          # View previous commits
# git diff                  # View changes not yet staged
# git status                # Check current Git status