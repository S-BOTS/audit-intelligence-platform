# Audit Intelligence Platform

### AI-Enabled Audit Analytics, Risk Scoring & Continuous Monitoring

The Audit Intelligence Platform is an evolving audit analytics project designed to automate transaction testing, identify risk indicators, prioritize audit exceptions, and support data-driven audit investigations.

The current version focuses on automated journal-entry analysis using Python, pandas, SQL, and configurable audit rules.

## Current Version

**Automated Journal Entry Auditor v0.1**

The tool analyzes a journal-entry population and identifies transactions that may require additional audit review.

A flagged transaction represents a risk indicator or audit exception and does not, by itself, constitute an audit finding.

## Current Audit Tests

The v0.1 engine currently evaluates:

- Weekend journal postings
- Potential duplicate transactions
- Round-dollar transactions
- High-value transactions
- Transaction-level risk scoring
- Low, Medium, and High risk classification
- Journal population analytics
- Activity analysis by journal preparer
- SQL and Python risk-score reconciliation

## Technology Stack

- Python
- pandas
- SQL / SQLite
- JSON configuration
- openpyxl
- Excel
- Git / GitHub 

# AI Audit Lab – Journal Entry Risk Analyzer

A Python-based audit analytics project designed to identify potentially high-risk journal entries and prioritize them for further audit investigation.

## Project Objective

Traditional exception testing can generate many individual exceptions for auditors to investigate. This project combines multiple audit risk indicators into a risk-scoring approach so that transactions exhibiting several risk characteristics can be prioritized.

The goal is not to conclude that an entry is fraudulent or erroneous, but to identify transactions that may warrant additional audit procedures.

## Current Audit Tests

The analyzer currently evaluates journal entries for:

- Weekend postings
- Round-dollar transactions
- High-value transactions
- Potential duplicate journal entries

## Risk Scoring

Each journal entry begins with a `Risk_Score` of 0.

One point is added when an entry meets each risk condition:

| Risk Indicator | Score |
|---|---:|
| Weekend posting | +1 |
| Round-dollar amount | +1 |
| Amount ≥ $5,000 | +1 |
| Potential duplicate | +1 |

Example:

A $10,000 journal posted on a weekend would receive:

- Weekend posting: +1
- Round-dollar amount: +1
- High-value transaction: +1

**Total Risk Score = 3**

Higher scores indicate that multiple risk indicators are present and can therefore help prioritize entries for further investigation.

## Technology

- Python
- pandas
- Excel
- Git
- GitHub

## Project Structure

```text
ai-audit-lab/
├── data/
│   └── Journal.csv
├── output/
│   └── audit_risk_report.xlsx
├── src/
│   └── journal_auditor.py
├── requirements.txt
├── .gitignore
└── README.md
```

## Output

The Python script produces a prioritized audit risk report containing journal information and calculated risk scores.

Entries are sorted from highest to lowest risk score and exported to:

```text
output/audit_risk_report.xlsx
```

## Audit Interpretation

A high risk score does **not** establish fraud, error, or control failure.

The score is a screening mechanism intended to help auditors focus further procedures on transactions displaying multiple risk characteristics.

## Planned Development

Future versions will expand the project with:

- Additional journal-entry risk indicators
- Configurable risk thresholds
- Weighted risk scoring
- User and account behavioral analysis
- Statistical anomaly detection
- Machine-learning-based risk identification
- Visualization and audit dashboards
- AI-assisted exception investigation
- Automated audit commentary

## Long-Term Goal

Develop this project into an AI-enabled continuous auditing framework that combines rule-based audit analytics, anomaly detection, machine learning, and AI-assisted investigation.