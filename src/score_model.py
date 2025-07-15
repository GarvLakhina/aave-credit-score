# Simple rule-based credit scoring model

import pandas as pd
import numpy as np

def quantile_normalize(series):
    # Returns a value between 0 and 1 based on rank
    return series.rank(method='average', pct=True)

def assign_scores(feature_df):
    # Quantile normalize features (higher is better)
    feature_df['q_num_deposits'] = quantile_normalize(feature_df['num_deposits'])
    feature_df['q_repay_borrow_ratio'] = quantile_normalize(feature_df['repay_borrow_ratio'])
    feature_df['q_activity_span_days'] = quantile_normalize(feature_df['activity_span_days'])
    feature_df['q_num_action_types'] = quantile_normalize(feature_df['num_action_types'])
    feature_df['q_avg_tx_amount'] = quantile_normalize(feature_df['avg_tx_amount'])
    feature_df['q_max_deposit'] = quantile_normalize(feature_df['max_deposit'])
    feature_df['q_max_borrow'] = quantile_normalize(feature_df['max_borrow'])
    feature_df['q_max_repay'] = quantile_normalize(feature_df['max_repay'])
    # Lower is better for penalties
    feature_df['q_std_tx_amount'] = 1 - quantile_normalize(feature_df['std_tx_amount'])
    feature_df['q_tx_frequency_per_day'] = quantile_normalize(feature_df['tx_frequency_per_day'])

    # Weighted sum (tune weights for best spread)
    score = (
        0.18 * feature_df['q_num_deposits'] +
        0.15 * feature_df['q_repay_borrow_ratio'] +
        0.13 * feature_df['q_activity_span_days'] +
        0.10 * feature_df['q_num_action_types'] +
        0.08 * feature_df['q_avg_tx_amount'] +
        0.06 * feature_df['q_max_deposit'] +
        0.06 * feature_df['q_max_borrow'] +
        0.06 * feature_df['q_max_repay'] +
        0.10 * feature_df['q_std_tx_amount'] +
        0.08 * feature_df['q_tx_frequency_per_day']
    )

    # Strong penalties for risky/bot-like behavior
    score -= 0.10 * feature_df['num_liquidations']
    # Penalize very high tx frequency (bots)
    score -= 0.10 * (feature_df['tx_frequency_per_day'] > 10)
    # Penalize very short avg time between txs (bots)
    score -= 0.10 * (feature_df['avg_time_between_txs'].fillna(1) < 0.01)

    # Min-max normalize to [0, 1]
    score = (score - score.min()) / (score.max() - score.min())
    feature_df['credit_score'] = (score * 1000).clip(0, 1000)
    return feature_df[['wallet', 'credit_score']]