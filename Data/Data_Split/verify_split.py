import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

print("=== SPLIT VERIFICATION ===")
manifest = pd.read_csv(ROOT / "Train" / "split_manifest.csv")
print(f"Total assets in manifest: {len(manifest)}")
print()

checks = [
    ("Crypto",      "Train/Crypto/BTC_features.csv",               "Test/Crypto/BTC_features.csv"),
    ("Commodities", "Train/Commodities/Gold_features.csv",          "Test/Commodities/Gold_features.csv"),
    ("ETFs",        "Train/ETFs/SPY_features.csv",                  "Test/ETFs/SPY_features.csv"),
    ("Futures",     "Train/Futures/NIFTY_50_Futures_features.csv",  "Test/Futures/NIFTY_50_Futures_features.csv"),
    ("Stocks",      "Train/Stocks/N50_HDFCBANK_features.csv",       "Test/Stocks/N50_HDFCBANK_features.csv"),
]

for cat, tr, te in checks:
    t = pd.read_csv(ROOT / tr)
    v = pd.read_csv(ROOT / te)
    t["Date"] = pd.to_datetime(t["Date"])
    v["Date"] = pd.to_datetime(v["Date"])
    overlap  = len(set(t["Date"]).intersection(set(v["Date"])))
    pct      = round(len(t) / (len(t) + len(v)) * 100, 1)
    train_end   = t["Date"].max().date()
    test_start  = v["Date"].min().date()
    no_leak = "OK" if overlap == 0 else f"LEAK! {overlap} overlapping dates"
    print(f"  {cat:12s}: train={len(t):5d} | test={len(v):5d} | split={pct}% | {no_leak}")
    print(f"               train ends {train_end}  /  test starts {test_start}")

print()
print("=== FOLDER FILE COUNTS ===")
for folder in ["Train", "Test"]:
    counts = []
    for cat in ["Crypto", "Commodities", "ETFs", "Futures", "Stocks"]:
        d = ROOT / folder / cat
        n = len(list(d.glob("*.csv"))) if d.exists() else 0
        counts.append(f"{cat}={n}")
    print(f"  {folder}: {', '.join(counts)}")

print()
print("=== SUMMARY ===")
by_cat = manifest.groupby("category")[["train", "test", "total"]].sum()
by_cat["split_pct"] = (by_cat["train"] / by_cat["total"] * 100).round(1)
print(by_cat.to_string())
