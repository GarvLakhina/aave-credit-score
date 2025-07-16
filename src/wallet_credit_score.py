import argparse
import json
import pandas as pd
from datetime import datetime
import numpy as np

# Define relevant action types
actions = ["deposit", "borrow", "repay", "redeemunderlying", "liquidationcall"]

def load_json_transactions(filepath):
    with open(filepath, 'r') as f:
        data = json.load(f)
    return data

def preprocess_transactions(data):
    rows = []
    for tx in data:
        wallet = tx.get('userWallet')
        action = tx.get('action')
        if action not in actions:
            continue
        amount = tx.get('amount')
        if amount is None and 'actionData' in tx:
            amount = tx['actionData'].get('amount', 0)
        amount = float(amount) if amount is not None else 0.0
        timestamp = int(tx.get('timestamp', 0))
        rows.append([wallet, action, amount, timestamp])
    df = pd.DataFrame(rows, columns=['wallet', 'action', 'amount', 'timestamp'])
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
    return df

def engineer_features(df):
    features = []
    for wallet, group in df.groupby('wallet'):
        feat = {}
        feat['wallet'] = wallet
        feat['num_deposits'] = len(group[group['action'] == 'deposit'])
        feat['num_borrows'] = len(group[group['action'] == 'borrow'])
        feat['num_repays'] = len(group[group['action'] == 'repay'])
        feat['num_liquidations'] = len(group[group['action'] == 'liquidationcall'])
        feat['total_deposits'] = group[group['action'] == 'deposit']['amount'].sum()
        feat['total_borrows'] = group[group['action'] == 'borrow']['amount'].sum()
        feat['total_repays'] = group[group['action'] == 'repay']['amount'].sum()
        if feat['total_borrows'] > 0:
            feat['repay_borrow_ratio'] = feat['total_repays'] / feat['total_borrows']
        else:
            feat['repay_borrow_ratio'] = 0
        dates = group['datetime'].sort_values()
        feat['activity_span_days'] = (dates.max() - dates.min()).days + 1 if not dates.empty else 0
        if len(dates) > 1:
            time_deltas = dates.diff().dt.total_seconds().dropna()
            feat['avg_time_between_txs'] = time_deltas.mean() / 86400
        else:
            feat['avg_time_between_txs'] = None
        feat['avg_tx_amount'] = group['amount'].mean() if not group['amount'].empty else 0
        feat['num_action_types'] = group['action'].nunique()
        feat['max_deposit'] = group[group['action'] == 'deposit']['amount'].max() if not group[group['action'] == 'deposit'].empty else 0
        feat['max_borrow'] = group[group['action'] == 'borrow']['amount'].max() if not group[group['action'] == 'borrow'].empty else 0
        feat['max_repay'] = group[group['action'] == 'repay']['amount'].max() if not group[group['action'] == 'repay'].empty else 0
        feat['std_tx_amount'] = group['amount'].std() if not group['amount'].empty else 0
        feat['tx_frequency_per_day'] = len(group) / feat['activity_span_days'] if feat['activity_span_days'] > 0 else len(group)
        if feat['total_deposits'] > 0:
            feat['borrow_deposit_ratio'] = feat['total_borrows'] / feat['total_deposits']
        else:
            feat['borrow_deposit_ratio'] = float('inf') if feat['total_borrows'] > 0 else 0
        features.append(feat)
    return pd.DataFrame(features)

def compute_score(row):
    score = 400
    score += min(row.get('num_deposits', 0), 10) * 10
    score += min(row.get('repay_borrow_ratio', 0), 2) * 100
    score += min(row.get('activity_span_days', 0), 180) * 1
    score += min(row.get('num_action_types', 0), 4) * 10
    score -= row.get('num_liquidations', 0) * 50
    borrow_dep = row.get('borrow_deposit_ratio', 0)
    if borrow_dep > 1.5:
        score -= min((borrow_dep - 1.5) * 100, 200)
    if row.get('total_repays', 0) == 0 and row.get('total_borrows', 0) > 0:
        score -= 100
    freq = row.get('tx_frequency_per_day', 0)
    if freq > 20:
        score -= 100
    elif freq < 0.1:
        score -= 20
    std_amt = row.get('std_tx_amount', 0)
    if std_amt > 50000:
        score -= 50
    if row.get('activity_span_days', 0) < 7:
        score -= 50
    return max(0, min(1000, score))

def assign_scores(feature_df):
    feature_df['raw_score'] = feature_df.apply(compute_score, axis=1)
    min_raw = feature_df['raw_score'].min()
    max_raw = feature_df['raw_score'].max()
    if max_raw == min_raw:
        feature_df['credit_score'] = 500.0
    else:
        feature_df['credit_score'] = ((feature_df['raw_score'] - min_raw) / (max_raw - min_raw) * 1000).round(2)
    return feature_df[['wallet', 'credit_score']]

def main():
    parser = argparse.ArgumentParser(description='Aave V2 Wallet Credit Scoring')
    parser.add_argument('--file', required=True, help='Path to sample_user_transactions.json')
    parser.add_argument('--output', default='wallet_scores.csv', help='Output CSV file for wallet scores')
    args = parser.parse_args()
    raw_data = load_json_transactions(args.file)
    df = preprocess_transactions(raw_data)
    features = engineer_features(df)
    scores = assign_scores(features)
    scores.to_csv(args.output, index=False)
    print(f"Saved wallet scores to {args.output}")

if __name__ == '__main__':
    main()
