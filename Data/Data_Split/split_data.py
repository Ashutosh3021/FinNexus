"""
Train/Test Time-Based Split — FinNexus
Splits Data/Features/**/*_features.csv into Train/ and Test/
using an 80/20 time-ordered split (no data leakage).

Excludes: Lead_features.csv (quality score 9/100)

Usage:
    python scripts/split_data.py
"""

from pathlib import Path
import pandas as pd

# ── Config ────────────────────────────────────────────────────────────────────
ROOT        = Path(__file__).resolve().parent.parent
FEATURES    = ROOT / "Data" / "Features"
TRAIN_ROOT  = ROOT / "Train"
TEST_ROOT   = ROOT / "Test"

SPLIT_RATIO = 0.80
EXCLUDE     = {"Lead_features"}          # stems to skip (quality too low)
CATEGORIES  = ["Crypto", "Commodities", "ETFs", "Futures", "Stocks"]

# ── Helpers ───────────────────────────────────────────────────────────────────

def split_dataset(src: Path, train_dst: Path, test_dst: Path) -> tuple[int, int]:
    """Time-based split. Returns (train_rows, test_rows)."""
    df = pd.read_csv(src)
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date").reset_index(drop=True)

    split_idx = int(len(df) * SPLIT_RATIO)
    train_df  = df.iloc[:split_idx]
    test_df   = df.iloc[split_idx:]

    train_dst.parent.mkdir(parents=True, exist_ok=True)
    test_dst.parent.mkdir(parents=True, exist_ok=True)

    train_df.to_csv(train_dst, index=False)
    test_df.to_csv(test_dst,  index=False)

    return len(train_df), len(test_df)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    total = skipped = errors = 0
    summary = []

    for cat in CATEGORIES:
        src_dir   = FEATURES / cat
        train_dir = TRAIN_ROOT / cat
        test_dir  = TEST_ROOT  / cat

        if not src_dir.exists():
            print(f"  [WARN] {cat}: source dir not found, skipping")
            continue

        files = sorted(src_dir.glob("*_features.csv"))
        cat_ok = cat_skip = 0

        for src in files:
            if src.stem in EXCLUDE:
                print(f"  [SKIP] {cat}/{src.name}  (excluded — low quality)")
                skipped += 1
                cat_skip += 1
                continue

            train_dst = train_dir / src.name
            test_dst  = test_dir  / src.name

            try:
                n_train, n_test = split_dataset(src, train_dst, test_dst)
                row_total = n_train + n_test
                if row_total == 0:
                    print(f"  [SKIP] {cat}/{src.name}  (0 rows after feature prep)")
                    skipped += 1
                    cat_skip += 1
                    continue
                total += 1
                cat_ok += 1
                summary.append({
                    "category":  cat,
                    "asset":     src.stem,
                    "train":     n_train,
                    "test":      n_test,
                    "total":     row_total,
                    "split_pct": round(n_train / row_total * 100, 1),
                })
            except Exception as e:
                print(f"  [ERROR] {cat}/{src.name}: {e}")
                errors += 1

        print(f"  [{cat}] {cat_ok} split, {cat_skip} skipped")

    # ── Summary ───────────────────────────────────────────────────────────────
    print()
    print("=" * 55)
    print(f"  Total split : {total}")
    print(f"  Skipped     : {skipped}")
    print(f"  Errors      : {errors}")
    print("=" * 55)

    if summary:
        df_sum = pd.DataFrame(summary)
        print()
        print("Per-category row counts:")
        print(df_sum.groupby("category")[["train","test","total"]].sum().to_string())
        print()
        print("Split % range (should be ~80%):")
        rng = df_sum.groupby("category")["split_pct"].agg(["min","max","mean"]).round(1)
        print(rng.to_string())

        # Save manifest
        manifest = ROOT / "Train" / "split_manifest.csv"
        df_sum.to_csv(manifest, index=False)
        print(f"\n  Manifest saved -> {manifest.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
