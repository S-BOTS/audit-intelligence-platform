import pandas as pd

from src.journal_auditor import (
    identify_weekend_entries,
    identify_duplicate_entries,
    identify_round_dollar_entries,
    identify_high_value_entries,
    calculate_risk_scores,
    classify_risk_levels
)


def test_identify_weekend_entries():
    """Confirm that Saturday and Sunday entries are flagged."""

    journal = pd.DataFrame({
        "Posting_Date": pd.to_datetime([
            "2026-11-02",  # Monday
            "2026-11-07",  # Saturday
            "2026-11-08"   # Sunday
        ])
    })

    result = identify_weekend_entries(journal)

    assert len(result) == 2

def test_identify_duplicate_entries():
    """Confirm that matching journal entries are flagged as duplicates."""

    journal = pd.DataFrame({
        "Posting_Date": pd.to_datetime([
            "2026-11-02",
            "2026-11-02",
            "2026-11-03"
        ]),
        "Account": ["5000", "5000", "6000"],
        "Description": ["Consulting", "Consulting", "Supplies"],
        "Amount": [5000.00, 5000.00, 2500.00],
        "Prepared_By": ["Sam", "Sam", "Alex"]
    })

    result = identify_duplicate_entries(journal)

    assert len(result) == 2

def test_identify_round_dollar_entries():
    """Confirm that transactions divisible by the configured base are flagged."""

    journal = pd.DataFrame({
        "Amount": [
            1000.00,
            2500.00,
            5000.00
        ]
    })

    result = identify_round_dollar_entries(
        journal,
        1000
    )

    assert len(result) == 2
def test_identify_high_value_entries():
    """Confirm that transactions at or above the threshold are flagged."""

    journal = pd.DataFrame({
        "Amount": [
            4999.99,
            5000.00,
            10000.00
        ]
    })

    result = identify_high_value_entries(
        journal,
        5000
    )

    assert len(result) == 2

def test_calculate_risk_scores():
    """Confirm that multiple risk indicators produce the correct score."""

    journal = pd.DataFrame({
        "Posting_Date": pd.to_datetime([
            "2026-11-07"
        ]),
        "Amount": [10000.00]
    })

    duplicate_entries = journal.iloc[0:0]

    risk_weights = {
        "weekend_posting": 1,
        "round_dollar": 1,
        "high_value": 2,
        "potential_duplicate": 3
    }

    result = calculate_risk_scores(
        journal,
        duplicate_entries,
        risk_weights,
        1000,
        5000
    )

    assert result.iloc[0]["Risk_Score"] == 4
def test_classify_risk_levels():
    """Confirm that risk scores are classified correctly."""

    journal = pd.DataFrame({
        "Risk_Score": [0, 2, 3, 7]
    })

    risk_levels = {
        "medium": 1,
        "high": 3
    }

    result = classify_risk_levels(
        journal,
        risk_levels
    )

    assert result["Risk_Level"].tolist() == [
        "Low",
        "Medium",
        "High",
        "High"
    ]