# Preprocessing script to extract features from raw Aave V2 transaction JSON

import json
import pandas as pd
from datetime import datetime

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
        # Try to get amount from top-level, else from actionData
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

        # Activity span
        dates = group['datetime'].sort_values()
        feat['activity_span_days'] = (dates.max() - dates.min()).days + 1 if not dates.empty else 0

        # New features
        # 1. Average time between transactions
        if len(dates) > 1:
            time_deltas = dates.diff().dt.total_seconds().dropna()
            feat['avg_time_between_txs'] = time_deltas.mean() / 86400  # in days
        else:
            feat['avg_time_between_txs'] = None

        # 2. Average transaction amount
        feat['avg_tx_amount'] = group['amount'].mean() if not group['amount'].empty else 0

        # 3. Number of unique action types
        feat['num_action_types'] = group['action'].nunique()

        # 4. Max single deposit/borrow/repay
        feat['max_deposit'] = group[group['action'] == 'deposit']['amount'].max() if not group[group['action'] == 'deposit'].empty else 0
        feat['max_borrow'] = group[group['action'] == 'borrow']['amount'].max() if not group[group['action'] == 'borrow'].empty else 0
        feat['max_repay'] = group[group['action'] == 'repay']['amount'].max() if not group[group['action'] == 'repay'].empty else 0

        # 5. Std deviation of transaction amounts
        feat['std_tx_amount'] = group['amount'].std() if not group['amount'].empty else 0

        # 6. Frequency of actions (txs per day)
        feat['tx_frequency_per_day'] = len(group) / feat['activity_span_days'] if feat['activity_span_days'] > 0 else len(group)

        features.append(feat)

    return pd.DataFrame(features)