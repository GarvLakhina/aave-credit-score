"""Generate score distribution plot and bucket statistics.
Run: python scripts/generate_analysis.py
Outputs:
 - results/score_distribution.png
 - results/bucket_counts.json
Prints bucket counts to stdout as JSON.
"""

import json
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE_DIR = Path(__file__).resolve().parents[1]
RESULTS_DIR = BASE_DIR / "results"
RESULTS_DIR.mkdir(exist_ok=True)
CSV_PATH = RESULTS_DIR / "wallet_scores.csv"

if not CSV_PATH.exists():
    raise FileNotFoundError(f"Scores file not found at {CSV_PATH}")

df = pd.read_csv(CSV_PATH)

# Plot distribution
plt.figure(figsize=(10, 5))
plt.hist(df["credit_score"], bins=20, color="skyblue", edgecolor="black")
plt.title("Wallet Credit Score Distribution")
plt.xlabel("Credit Score")
plt.ylabel("Number of Wallets")
plt.tight_layout()
IMG_PATH = RESULTS_DIR / "score_distribution.png"
plt.savefig(IMG_PATH, dpi=150)
print(f"Saved distribution plot to {IMG_PATH}")

# Bucket statistics
buckets = [(0, 299), (300, 499), (500, 699), (700, 799), (800, 899), (900, 1000)]
counts = {
    f"{low}-{high}": int(((df["credit_score"] >= low) & (df["credit_score"] <= high)).sum())
    for low, high in buckets
}
JSON_PATH = RESULTS_DIR / "bucket_counts.json"
JSON_PATH.write_text(json.dumps(counts, indent=2))
print(json.dumps(counts))
