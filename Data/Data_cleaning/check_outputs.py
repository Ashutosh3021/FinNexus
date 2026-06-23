import pandas as pd
import json

print("=== FEATURE COLUMN COUNTS ===")
samples = {
    "BTC (Crypto)":     "Data/Features/Crypto/BTC_features.csv",
    "Gold (Commodity)": "Data/Features/Commodities/Gold_features.csv",
    "SPY (ETF)":        "Data/Features/ETFs/SPY_features.csv",
    "HDFCBANK (Stock)": "Data/Features/Stocks/N50_HDFCBANK_features.csv",
    "NIFTY Futures":    "Data/Features/Futures/NIFTY_50_Futures_features.csv",
}
for label, path in samples.items():
    df = pd.read_csv(path)
    print(f"  {label}: {len(df)} rows x {len(df.columns)} cols")

print()
print("=== QUALITY SCORES BY CATEGORY ===")
for cat in ["Crypto", "ETFs", "Commodities", "Futures"]:
    with open(f"Reports/Data_Quality_{cat}.json") as f:
        reports = json.load(f)
    scores = [r.get("quality_score", 0) for r in reports if "quality_score" in r]
    if scores:
        print(f"  {cat}: avg={sum(scores)/len(scores):.1f}  min={min(scores):.1f}  max={max(scores):.1f}")

print()
print("=== STOCK QUALITY SAMPLE ===")
with open("Reports/Data_Quality_Stocks.json") as f:
    stock_reports = json.load(f)
scores = [r.get("quality_score", 0) for r in stock_reports if "quality_score" in r]
print(f"  Stocks ({len(scores)} assets): avg={sum(scores)/len(scores):.1f}  min={min(scores):.1f}  max={max(scores):.1f}")

print()
print("=== LEAD (DATA ISSUE FLAGGED) ===")
with open("Reports/Data_Quality_Commodities.json") as f:
    comm_reports = json.load(f)
for r in comm_reports:
    if r.get("asset") == "Lead":
        print(f"  Lead: quality={r.get('quality_score')}  original_rows={r.get('original_rows')}  final_rows={r.get('final_rows')}")
        for issue in r.get("issues", []):
            print(f"    [!] {issue}")

print()
print("=== FEATURE COLUMNS (BTC sample) ===")
df = pd.read_csv("Data/Features/Crypto/BTC_features.csv")
base = {"Date","Open","High","Low","Close","Volume","is_outlier","data_quality"}
feat_cols = [c for c in df.columns if c not in base]
print(f"  Total feature columns: {len(feat_cols)}")
print(f"  First 20: {feat_cols[:20]}")
print(f"  Last 10:  {feat_cols[-10:]}")
