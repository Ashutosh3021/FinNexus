"""
Main Data Pipeline Runner — FinNexus
Orchestrates: load → clean → feature engineering → EDA → save

Usage:
    python -m Backend.data.pipeline                  # all categories
    python -m Backend.data.pipeline --category Crypto
    python -m Backend.data.pipeline --category Stocks --skip-eda
"""

import argparse
import json
import logging
import sys
from pathlib import Path

import pandas as pd

# ─── Path Setup ───────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[2]      # FinNexus/
DATA_ROOT = ROOT / "Data"
CLEANED_ROOT = ROOT / "Data" / "Cleaned"
FEATURES_ROOT = ROOT / "Data" / "Features"
REPORTS_ROOT = ROOT / "Reports"

sys.path.insert(0, str(ROOT))

from Backend.data.cleaner import clean_dataset
from Backend.data.features import (
    create_technical_features,
    create_all_targets,
    create_context_features,
    prepare_features,
)
from Backend.data.eda import (
    generate_eda_report,
    compute_asset_stats,
    plot_correlation_matrix,
    plot_performance_ranking,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ─── Category Config ──────────────────────────────────────────────────────────
# Each entry: (category_label, raw_dir, asset_type, file_pattern, symbol_extractor)
# symbol_extractor: callable(Path) -> str

def _symbol_direct(p: Path) -> str:
    """File is named {SYMBOL}.csv → symbol = stem."""
    return p.stem

def _symbol_stock(p: Path) -> str:
    """File is named {INDEX}_{TICKER}.csv → return full stem."""
    return p.stem   # e.g. "N50_HDFCBANK"

CATEGORIES = {
    "Crypto": {
        "raw_dir": DATA_ROOT / "Crypto",
        "asset_type": "crypto",
        "pattern": "*.csv",
        "symbol_fn": _symbol_direct,
        "exclude": ["MASTER_SUMMARY"],       # skip summary files
        "exclude_suffix": ["_metadata"],
        "context_asset": "BTC",              # market reference for context features
    },
    "Commodities": {
        "raw_dir": DATA_ROOT / "Commodities",
        "asset_type": "commodity",
        "pattern": "*.csv",
        "symbol_fn": _symbol_direct,
        "exclude": ["MASTER_SUMMARY"],
        "exclude_suffix": [],
        "context_asset": None,
    },
    "ETFs": {
        "raw_dir": DATA_ROOT / "ETF",
        "asset_type": "etf",
        "pattern": "*.csv",
        "symbol_fn": _symbol_direct,
        "exclude": ["MASTER_SUMMARY"],
        "exclude_suffix": ["_metadata"],
        "context_asset": "SPY",
    },
    "Stocks": {
        "raw_dir": DATA_ROOT / "Stock",
        "asset_type": "stock",
        "pattern": "*.csv",
        "symbol_fn": _symbol_stock,
        "exclude": ["MASTER_SUMMARY", "N50", "NMidcap", "NSmallcap", "NNext"],
        "exclude_suffix": ["_metadata"],
        "context_asset": "N50",              # use Nifty 50 index as market context
    },
    "Futures": {
        "raw_dir": DATA_ROOT / "Futures_Options",
        "asset_type": "futures",
        "pattern": "*.csv",
        "symbol_fn": _symbol_direct,
        "exclude": ["MASTER_SUMMARY"],
        "exclude_suffix": [],
        "context_asset": None,
    },
}


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _load_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(str(path))
    return df


def _should_skip(path: Path, cfg: dict) -> bool:
    stem = path.stem
    if stem in cfg["exclude"]:
        return True
    for suf in cfg["exclude_suffix"]:
        if stem.endswith(suf):
            return True
    return False


def _get_market_df(cfg: dict, cleaned_assets: dict) -> pd.DataFrame | None:
    """Return the market reference dataframe for context feature calculation."""
    ctx = cfg.get("context_asset")
    if not ctx:
        return None
    # Try exact key, or prefix match (for Stocks: 'N50')
    if ctx in cleaned_assets:
        return cleaned_assets[ctx]
    for k, v in cleaned_assets.items():
        if k.startswith(ctx):
            return v
    return None


def _save_csv(df: pd.DataFrame, output_dir: Path, symbol: str, stage: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"{symbol}_{stage}.csv"
    df.to_csv(str(out_path), index=False)


# ─── Core Pipeline ────────────────────────────────────────────────────────────

def run_category(
    category: str,
    skip_eda: bool = False,
    skip_features: bool = False,
    max_assets: int = None,
) -> dict:
    """
    Run the full pipeline for one category.
    Returns a summary dict.
    """
    cfg = CATEGORIES[category]
    raw_dir: Path = cfg["raw_dir"]
    asset_type: str = cfg["asset_type"]

    if not raw_dir.exists():
        logger.error(f"[{category}] Raw data dir not found: {raw_dir}")
        return {}

    # Discover files
    all_files = [
        p for p in sorted(raw_dir.glob(cfg["pattern"]))
        if not _should_skip(p, cfg)
    ]
    if max_assets:
        all_files = all_files[:max_assets]

    logger.info(f"[{category}] Processing {len(all_files)} assets")

    quality_reports = []
    cleaned_assets = {}
    feature_assets = {}
    all_stats = []

    # ── Phase 1: Clean ────────────────────────────────────────────────────────
    logger.info(f"[{category}] Phase 1: Cleaning …")
    clean_out = CLEANED_ROOT / category
    for path in all_files:
        symbol = cfg["symbol_fn"](path)
        try:
            raw = _load_csv(path)
            cleaned, report = clean_dataset(raw, asset_name=symbol, asset_type=asset_type)
            quality_reports.append(report)
            cleaned_assets[symbol] = cleaned
            _save_csv(cleaned, clean_out, symbol, "cleaned")
        except Exception as e:
            logger.error(f"  [{symbol}] clean failed: {e}")
            quality_reports.append({"asset": symbol, "error": str(e)})

    # ── Phase 2: Feature Engineering ─────────────────────────────────────────
    if not skip_features:
        logger.info(f"[{category}] Phase 2: Feature engineering …")
        feat_out = FEATURES_ROOT / category
        market_df = _get_market_df(cfg, cleaned_assets)

        for symbol, df in cleaned_assets.items():
            try:
                feat_df = create_technical_features(df)
                feat_df = create_all_targets(feat_df)

                if market_df is not None and symbol != cfg.get("context_asset"):
                    market_label = cfg["context_asset"].lower()
                    feat_df = create_context_features(
                        feat_df, market_df, market_label=market_label
                    )

                feat_df = prepare_features(feat_df, target_col="target_7d")
                feature_assets[symbol] = feat_df
                _save_csv(feat_df, feat_out, symbol, "features")
            except Exception as e:
                logger.error(f"  [{symbol}] feature engineering failed: {e}")

    # ── Phase 3: EDA ──────────────────────────────────────────────────────────
    if not skip_eda and cleaned_assets:
        logger.info(f"[{category}] Phase 3: EDA …")
        try:
            eda_summary = generate_eda_report(
                assets=cleaned_assets,
                category=category,
                output_dir=REPORTS_ROOT,
            )
            all_stats = list(eda_summary.get("assets", {}).values())
        except Exception as e:
            logger.error(f"[{category}] EDA failed: {e}")

    # ── Save data quality report ───────────────────────────────────────────────
    _save_quality_report(quality_reports, category)

    logger.info(f"[{category}] Done. Cleaned={len(cleaned_assets)}, Features={len(feature_assets)}")
    return {
        "category": category,
        "n_cleaned": len(cleaned_assets),
        "n_features": len(feature_assets),
        "quality_reports": quality_reports,
        "asset_stats": all_stats,
    }


def run_all(
    categories: list = None,
    skip_eda: bool = False,
    skip_features: bool = False,
    max_assets: int = None,
) -> None:
    """Run pipeline for all (or selected) categories, then generate cross-asset reports."""
    if categories is None:
        categories = list(CATEGORIES.keys())

    all_results = {}
    all_cleaned = {}   # {symbol: df} across categories — for correlation matrix
    all_stats = []

    for cat in categories:
        result = run_category(
            cat,
            skip_eda=skip_eda,
            skip_features=skip_features,
            max_assets=max_assets,
        )
        all_results[cat] = result
        # Collect cleaned for cross-category correlation
        clean_dir = CLEANED_ROOT / cat
        if clean_dir.exists():
            for p in clean_dir.glob("*_cleaned.csv"):
                sym = p.stem.replace("_cleaned", "")
                df = pd.read_csv(str(p))
                df["Date"] = pd.to_datetime(df["Date"])
                all_cleaned[sym] = df
        all_stats.extend(result.get("asset_stats", []))

    # Cross-asset correlation matrix
    if not skip_eda and len(all_cleaned) >= 2:
        logger.info("Generating cross-asset correlation matrix …")
        try:
            corr_path = REPORTS_ROOT / "Correlation_Matrix.png"
            plot_correlation_matrix(
                all_cleaned,
                output_path=corr_path,
                title="FinNexus — All Assets Correlation Matrix (Daily Returns)",
            )
        except Exception as e:
            logger.error(f"Correlation matrix failed: {e}")

    # Performance ranking
    if not skip_eda and all_stats:
        logger.info("Generating performance ranking …")
        try:
            rank_path = REPORTS_ROOT / "Performance_Ranking.png"
            plot_performance_ranking(
                all_stats,
                output_path=rank_path,
                metric="sharpe_ratio",
                title="FinNexus — All Assets: Sharpe Ratio Ranking",
            )
        except Exception as e:
            logger.error(f"Performance ranking failed: {e}")

    # Save master summary JSON
    _save_master_summary(all_results, all_stats)
    logger.info("Pipeline complete.")


# ─── Reporting Utilities ──────────────────────────────────────────────────────

def _save_quality_report(reports: list, category: str) -> None:
    REPORTS_ROOT.mkdir(parents=True, exist_ok=True)
    out = REPORTS_ROOT / f"Data_Quality_{category}.json"
    with open(str(out), "w") as f:
        json.dump(reports, f, indent=2, default=str)

    # Human-readable text summary
    txt_out = REPORTS_ROOT / "Data_Quality_Report.txt"
    mode = "a" if txt_out.exists() else "w"
    with open(str(txt_out), mode, encoding="utf-8") as f:
        f.write(f"\n{'='*60}\n{category.upper()} — Data Quality Report\n{'='*60}\n")
        for r in reports:
            name = r.get("asset", "?")
            if "error" in r:
                f.write(f"  [{name}] ERROR: {r['error']}\n")
                continue
            score = r.get("quality_score", "?")
            issues = r.get("issues", [])
            miss = r.get("missing_pct", "?")
            outliers = r.get("outlier_rows", 0)
            f.write(
                f"  [{name}] score={score}/100 | missing={miss}% | "
                f"outliers={outliers} | issues={len(issues)}\n"
            )
            for issue in issues:
                f.write(f"       [!] {issue}\n")


def _save_master_summary(all_results: dict, all_stats: list) -> None:
    REPORTS_ROOT.mkdir(parents=True, exist_ok=True)

    # Insights document
    insights_path = REPORTS_ROOT / "Key_Insights.md"
    with open(str(insights_path), "w", encoding="utf-8") as f:
        f.write("# FinNexus — Key EDA Insights\n\n")
        f.write("## Summary by Category\n\n")
        for cat, res in all_results.items():
            f.write(f"### {cat}\n")
            f.write(f"- Assets cleaned: {res.get('n_cleaned', 0)}\n")
            f.write(f"- Feature sets created: {res.get('n_features', 0)}\n\n")

        if all_stats:
            df_stats = pd.DataFrame(all_stats)
            f.write("## Top Performers by Sharpe Ratio\n\n")
            top = df_stats.dropna(subset=["sharpe_ratio"]).nlargest(10, "sharpe_ratio")
            f.write("| Asset | Sharpe | Annual Return% | Max Drawdown% |\n")
            f.write("|-------|--------|---------------|---------------|\n")
            for _, row in top.iterrows():
                f.write(
                    f"| {row.get('asset','?')} | {row.get('sharpe_ratio','?')} | "
                    f"{row.get('annual_return_pct','?')} | {row.get('max_drawdown_pct','?')} |\n"
                )

            f.write("\n## Feature Dictionary\n\n")
            f.write(_feature_dictionary())

    logger.info(f"Insights saved → {insights_path}")


def _feature_dictionary() -> str:
    rows = [
        ("return_1d", "1-day price return", "(p_t - p_t-1) / p_t-1", "All"),
        ("return_7d", "7-day price return", "(p_t - p_t-7) / p_t-7", "All"),
        ("return_30d", "30-day price return", "(p_t - p_t-30) / p_t-30", "All"),
        ("log_return_1d", "Log daily return", "ln(p_t / p_t-1)", "All"),
        ("sma_20/50/100/200", "Simple Moving Averages", "rolling mean", "All"),
        ("ema_12/26", "Exponential Moving Averages", "ewm(span=12/26)", "All"),
        ("dist_from_sma_50", "Distance from SMA50", "(close - sma50) / sma50", "All"),
        ("rsi_14", "Relative Strength Index", "Wilder RSI(14)", "All"),
        ("macd_line", "MACD line", "ema12 - ema26", "All"),
        ("macd_signal", "MACD signal", "ema9 of macd_line", "All"),
        ("macd_histogram", "MACD histogram", "macd_line - macd_signal", "All"),
        ("bb_upper/lower/middle", "Bollinger Bands", "SMA20 ± 2σ", "All"),
        ("bb_bandwidth", "BB bandwidth", "(upper-lower)/middle", "All"),
        ("bb_pct_b", "BB %B position", "(close-lower)/(upper-lower)", "All"),
        ("atr_14", "Average True Range", "ewm TR(14)", "All"),
        ("adx_14", "Average Directional Index", "Wilder ADX(14)", "All"),
        ("stoch_k/d", "Stochastic Oscillator", "%K(14), %D(3)", "All"),
        ("obv", "On-Balance Volume", "cumulative signed volume", "All"),
        ("vwap_20d", "VWAP 20-day", "sum(TP*V)/sum(V) over 20d", "All"),
        ("vol_30d", "Annualised volatility 30d", "std(log_ret,30d)*√252", "All"),
        ("vol_60d", "Annualised volatility 60d", "std(log_ret,60d)*√252", "All"),
        ("parkinson_vol_30d", "Parkinson estimator", "high/low log range", "All"),
        ("golden_cross", "SMA50 > SMA200", "binary", "All"),
        ("price_to_high_1yr", "Price / 52-week high", "close/rolling_high(252)", "All"),
        ("day_range_pct", "Intraday range %", "(high-low)/close", "All"),
        ("target_7d", "7-day forward return label", "1 if p_t+7 > p_t", "All"),
        ("corr_btc_30d", "30d rolling BTC correlation", "rolling corr of returns", "Crypto"),
        ("corr_n50_30d", "30d rolling Nifty50 correlation", "rolling corr of returns", "Stocks"),
        ("beta_btc_30d", "Rolling beta vs BTC", "cov/var over 30d", "Crypto"),
    ]
    header = "| Feature | Description | Formula | Asset Type |\n"
    sep = "|---------|-------------|---------|------------|\n"
    body = "".join(
        f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} |\n" for r in rows
    )
    return header + sep + body


# ─── Entry Point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FinNexus Data Pipeline")
    parser.add_argument(
        "--category",
        choices=list(CATEGORIES.keys()) + ["all"],
        default="all",
        help="Which category to process (default: all)",
    )
    parser.add_argument("--skip-eda", action="store_true", help="Skip EDA report generation")
    parser.add_argument("--skip-features", action="store_true", help="Skip feature engineering")
    parser.add_argument("--max-assets", type=int, default=None,
                        help="Limit to N assets per category (for testing)")
    args = parser.parse_args()

    cats = list(CATEGORIES.keys()) if args.category == "all" else [args.category]
    run_all(
        categories=cats,
        skip_eda=args.skip_eda,
        skip_features=args.skip_features,
        max_assets=args.max_assets,
    )
