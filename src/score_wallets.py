# Entry point: JSON in → CSV with scores out

import argparse
import pandas as pd
from preprocess import load_json_transactions, preprocess_transactions, engineer_features
from score_model import assign_scores

def main(input_path, output_path):
    raw_data = load_json_transactions(input_path)
    df = preprocess_transactions(raw_data)
    features = engineer_features(df)
    scores = assign_scores(features)
    scores.to_csv(output_path, index=False)
    print(f"Saved wallet scores to {output_path}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True, help='Path to user-transactions.json')
    parser.add_argument('--output', required=True, help='CSV output path for scores')
    args = parser.parse_args()
    main(args.input, args.output)