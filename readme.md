# Aave V2 Wallet Credit Scoring

This project provides a transparent, explainable credit scoring model for Aave V2 wallets using transaction-level data. The model is designed for clarity, robustness, and practical risk assessment, making it suitable for internship submissions, technical interviews, or DeFi analytics portfolios.

---

## Table of Contents
- [Overview](#overview)
- [Credit Score Philosophy](#credit-score-philosophy)
- [Feature Engineering](#feature-engineering)
- [Scoring Logic](#scoring-logic)
- [Score Distribution](#score-distribution)
- [How to Run](#how-to-run)
- [Project Structure](#project-structure)
- [Sample Output](#sample-output)
- [Notes & Further Improvements](#notes--further-improvements)

---

## Overview
- **Goal:** Assign a credit score (0–1000) to each wallet based on its Aave V2 transaction history.
- **Input:** JSON file of user-level Aave V2 transactions (`data/sample_user_transactions.json`).
- **Output:** CSV of wallet addresses and credit scores (`results/wallet_scores.csv`), plus distribution plot and bucket stats.
- **Design:** Fully deterministic, interpretable, and robust to edge cases; no black-box ML.

---

## Credit Score Philosophy
The model reflects real-world credit risk principles, adapted for DeFi:

| Score Range | Category         | Description                      |
|-------------|------------------|----------------------------------|
| 0–299       | Critical/Bot     | Liquidations, bots, high risk    |
| 300–499     | Poor             | High leverage, low activity      |
| 500–699     | Fair/Average     | Typical user, some risk          |
| 700–799     | Good             | Healthy, diversified, low risk   |
| 800–899     | Very Good        | Reliable, consistent, low risk   |
| 900–1000    | Excellent        | Long-term, diverse, no risk      |

- **Rewards:** Deposits, repayments, longevity, action diversity
- **Penalties:** Liquidations, over-borrowing, inactivity, bot-like frequency, erratic sizes
- **Neutrality:** Final scores are linearly rescaled to 0–1000 for a full spread, preserving wallet order

---

## Feature Engineering
Features are engineered per wallet using transaction-level data:
- Number of deposits, borrows, repays, liquidations
- Total and max amounts for each action
- Repay/borrow ratio
- Activity span (days between first and last tx)
- Average time between transactions
- Average and std deviation of transaction amounts
- Number of unique action types
- Transaction frequency per day
- Borrow/deposit ratio (riskiness)

---

## Scoring Logic
1. **Raw Additive Score:**
   - Starts at 400
   - Rewards for deposits, repay/borrow ratio, longevity, action diversity
   - Penalties for liquidations, high leverage, no repayments, bot-like frequency, erratic tx sizes, short lifespan
2. **Linear Min-Max Scaling:**
   - Raw scores are linearly mapped to [0, 1000] across the dataset
   - Ensures full use of the score range and neutral, dataset-relative distribution
3. **No Black-Box ML:**
   - All logic is rule-based and easily auditable

---

## Score Distribution
Example bucket counts (after normalization):

| Bucket    | Wallets |
|-----------|---------|
| 0–299     | 42      |
| 300–499   | 698     |
| 500–699   | 1957    |
| 700–799   | 324     |
| 800–899   | 346     |
| 900–1000  | 120     |

![Score Distribution](results/score_distribution.png)

---

## How to Run
**Requirements:** Python 3.10+, pandas, matplotlib

1. Install dependencies (if needed):
   ```bash
   pip install pandas matplotlib
   ```
2. Run the scoring pipeline:
   ```bash
   python src/score_wallets.py --input data/sample_user_transactions.json --output results/wallet_scores.csv
   ```
3. Generate analysis/plot:
   ```bash
   python scripts/generate_analysis.py
   ```
4. Check `results/score_distribution.png` and `results/bucket_counts.json`

---

## Project Structure
```
├── data/
│   └── sample_user_transactions.json   # Input transaction data
├── results/
│   ├── wallet_scores.csv              # Output scores
│   ├── score_distribution.png         # Score histogram
│   └── bucket_counts.json             # Score buckets
├── src/
│   ├── preprocess.py                  # Feature engineering
│   ├── score_model.py                 # Scoring logic
│   └── score_wallets.py               # Pipeline entry point
├── scripts/
│   └── generate_analysis.py           # Plotting/statistics
└── README.md
```

---

## Sample Output
| wallet                                  | credit_score |
|------------------------------------------|--------------|
| 0x00000000001accfa9cef68cf5371a23025b6d4b6 | 151.13      |
| 0x0000000002032370b971dabd36d72f3e5a7bf1ee | 979.70      |
| ...                                      | ...          |

---

## Notes & Further Improvements
- **Explainability:** All scoring steps are transparent and easily auditable
- **Robustness:** Handles missing data, outliers, and blank scores
- **Extensibility:** Easy to add new features or adjust weights/rules
- **Further work:**
  - Explore anomaly/bot detection
  - Add more domain-specific features
  - Test on larger/more diverse datasets

---

**Author:** Garv Lakhina

For questions or improvements, please open an issue or fork the repo.