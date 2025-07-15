# Simple rule-based credit scoring model

import pandas as pd
import numpy as np

# Deterministic additive credit scoring reflecting the stated philosophy

def quantile_normalize(series):
    """Return percentile ranks (0-1) for a numeric pandas Series."""
    return series.rank(method='average', pct=True)

def compute_score(row):
    # Base score gives room for penalties and rewards
    score = 400

    # Positive contributions
    score += min(row.get('num_deposits', 0), 10) * 10  # up to +100
    score += min(row.get('repay_borrow_ratio', 0), 2) * 100  # up to +200
    score += min(row.get('activity_span_days', 0), 180) * 1  # up to +180
    score += min(row.get('num_action_types', 0), 4) * 10  # up to +40 for diversity

    # Negative contributions / penalties
    score -= row.get('num_liquidations', 0) * 50  # strong penalty

    # High leverage / over-borrowing penalty
    borrow_dep = row.get('borrow_deposit_ratio', 0)
    if borrow_dep > 1.5:
        score -= min((borrow_dep - 1.5) * 100, 200)

    # No repayments at all but has borrows ➔ risky
    if row.get('total_repays', 0) == 0 and row.get('total_borrows', 0) > 0:
        score -= 100

    # Bot-like high frequency
    freq = row.get('tx_frequency_per_day', 0)
    if freq > 20:
        score -= 100
    elif freq < 0.1:  # nearly inactive
        score -= 20

    # Erratic transaction size penalty
    std_amt = row.get('std_tx_amount', 0)
    if std_amt > 50000:
        score -= 50

    # Very short-lived wallet penalty
    if row.get('activity_span_days', 0) < 7:
        score -= 50

    # Clip to 0-1000
    return max(0, min(1000, score))

def assign_scores(feature_df):
    """Compute deterministic raw scores then linearly rescale to 0-1000.

    This keeps the interpretability of the additive `compute_score` while
    guaranteeing that every run fills the full credit-score bandwidth, giving a
    neutral, well-spread distribution no matter the dataset size.
    """
    # 1. Row-level raw additive score (transparent)
    feature_df['raw_score'] = feature_df.apply(compute_score, axis=1)

    # 2. Linear min-max rescaling across the dataset → [0, 1000]
    min_raw = feature_df['raw_score'].min()
    max_raw = feature_df['raw_score'].max()

    if max_raw == min_raw:
        # Degenerate case: all wallets identical → assign mid band
        feature_df['credit_score'] = 500.0
    else:
        feature_df['credit_score'] = ((feature_df['raw_score'] - min_raw) / (max_raw - min_raw) * 1000).round(2)

    return feature_df[['wallet', 'credit_score']]