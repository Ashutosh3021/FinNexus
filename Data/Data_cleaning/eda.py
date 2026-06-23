"""
EDA Module — FinNexus
Generates statistical reports and visualisations for each asset category.
"""

import logging
import warnings
from pathlib import Path
from typing import Optional

import matplotlib
matplotlib.use("Agg")  # non-interactive backend for server/batch use
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages

warnings.filterwarnings("ignore")
logger = logging.getLogger(__name__)

FIGURE_DPI = 120
PLOT_STYLE = "seaborn-v0_8-darkgrid"
plt.style.use(PLOT_STYLE)


# ─── Public API ───────────────────────────────────────────────────────────────

def generate_eda_report(
    assets: dict,  # {asset_name: df}
    category: str,
    output_dir: Path,
) -> dict:
    """
    Generate full EDA report for a category (PDF + summary dict).

    Parameters
    ----------
    assets     : dict mapping asset_name → cleaned DataFrame
    category   : e.g. 'Crypto', 'Stocks', 'Commodities', 'ETFs'
    output_dir : Where to write the PDF and PNG files

    Returns
    -------
    summary : dict with per-asset stats and cross-asset metrics
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    pdf_path = output_dir / f"EDA_{category}.pdf"
    summary = {"category": category, "assets": {}}

    with PdfPages(str(pdf_path)) as pdf:
        # Cover page
        _add_cover_page(pdf, category, list(assets.keys()))

        for name, df in assets.items():
            if df is None or len(df) < 30:
                logger.warning(f"[{name}] too few rows, skipping EDA")
                continue
            logger.info(f"  → EDA: {name}")
            stats = compute_asset_stats(df, name)
            summary["assets"][name] = stats

            # Per-asset pages
            _page_price_analysis(pdf, df, name)
            _page_returns_analysis(pdf, df, name)
            _page_volume_analysis(pdf, df, name)
            _page_volatility_analysis(pdf, df, name)
            _page_risk_metrics(pdf, df, name, stats)

    logger.info(f"[{category}] PDF saved → {pdf_path}")
    return summary


def compute_asset_stats(df: pd.DataFrame, asset_name: str) -> dict:
    """Compute summary statistics for a single asset."""
    close = df["Close"].dropna()
    if len(close) < 2:
        return {}

    daily_ret = close.pct_change().dropna()
    log_ret = np.log(close / close.shift(1)).dropna()
    annual_factor = np.sqrt(252)

    vol_30d = log_ret.rolling(30).std().iloc[-1] * annual_factor if len(log_ret) >= 30 else np.nan
    vol_60d = log_ret.rolling(60).std().iloc[-1] * annual_factor if len(log_ret) >= 60 else np.nan

    # Max drawdown
    cumulative = (1 + daily_ret).cumprod()
    peak = cumulative.expanding().max()
    drawdown = (cumulative - peak) / peak
    max_dd = float(drawdown.min())

    # Sharpe (assuming 0 risk-free rate for simplicity)
    ann_ret = float(daily_ret.mean() * 252)
    ann_vol = float(daily_ret.std() * annual_factor)
    sharpe = ann_ret / ann_vol if ann_vol > 0 else np.nan

    # Sortino
    downside = daily_ret[daily_ret < 0].std() * annual_factor
    sortino = ann_ret / downside if downside > 0 else np.nan

    # Calmar
    calmar = ann_ret / abs(max_dd) if max_dd != 0 else np.nan

    # VaR 95%
    var_95 = float(daily_ret.quantile(0.05))

    # Total return
    total_ret = float((close.iloc[-1] / close.iloc[0]) - 1)

    return {
        "asset": asset_name,
        "start_date": str(close.index[0] if isinstance(close.index[0], pd.Timestamp) else df["Date"].iloc[0]),
        "end_date": str(close.index[-1] if isinstance(close.index[-1], pd.Timestamp) else df["Date"].iloc[-1]),
        "n_rows": len(df),
        "price_min": float(close.min()),
        "price_max": float(close.max()),
        "price_mean": float(close.mean()),
        "price_last": float(close.iloc[-1]),
        "total_return_pct": round(total_ret * 100, 2),
        "annual_return_pct": round(ann_ret * 100, 2),
        "ann_volatility": round(ann_vol, 4),
        "vol_30d": round(vol_30d, 4) if not np.isnan(vol_30d) else None,
        "vol_60d": round(vol_60d, 4) if not np.isnan(vol_60d) else None,
        "sharpe_ratio": round(sharpe, 3) if not np.isnan(sharpe) else None,
        "sortino_ratio": round(sortino, 3) if not np.isnan(sortino) else None,
        "calmar_ratio": round(calmar, 3) if not np.isnan(calmar) else None,
        "max_drawdown_pct": round(max_dd * 100, 2),
        "var_95_pct": round(var_95 * 100, 3),
        "skewness": round(float(daily_ret.skew()), 4),
        "kurtosis": round(float(daily_ret.kurt()), 4),
    }


def plot_correlation_matrix(
    assets: dict,  # {name: df}
    output_path: Path,
    title: str = "Asset Correlation Matrix",
) -> pd.DataFrame:
    """
    Compute and plot pairwise correlation of daily returns for all assets.
    Saves a PNG and returns the correlation DataFrame.
    """
    returns = {}
    for name, df in assets.items():
        if df is None or "Close" not in df.columns:
            continue
        r = df.set_index("Date")["Close"].pct_change().rename(name)
        returns[name] = r

    if len(returns) < 2:
        logger.warning("Not enough assets for correlation matrix.")
        return pd.DataFrame()

    ret_df = pd.DataFrame(returns)
    corr = ret_df.corr()

    fig, ax = plt.subplots(figsize=(max(10, len(corr) * 0.6), max(8, len(corr) * 0.5)))
    import matplotlib.colors as mcolors
    cmap = plt.cm.RdYlGn
    im = ax.imshow(corr.values, cmap=cmap, vmin=-1, vmax=1, aspect="auto")
    plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    ax.set_xticks(range(len(corr.columns)))
    ax.set_yticks(range(len(corr.index)))
    ax.set_xticklabels(corr.columns, rotation=90, fontsize=8)
    ax.set_yticklabels(corr.index, fontsize=8)
    # Annotate cells
    for i in range(len(corr)):
        for j in range(len(corr.columns)):
            val = corr.values[i, j]
            ax.text(j, i, f"{val:.2f}", ha="center", va="center", fontsize=6,
                    color="black" if abs(val) < 0.7 else "white")
    ax.set_title(title, fontsize=13, fontweight="bold", pad=12)
    fig.tight_layout()
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(str(output_path), dpi=FIGURE_DPI, bbox_inches="tight")
    plt.close(fig)
    logger.info(f"Correlation matrix saved → {output_path}")
    return corr


def plot_performance_ranking(
    stats_list: list,  # list of dicts from compute_asset_stats
    output_path: Path,
    metric: str = "sharpe_ratio",
    title: str = "Performance Ranking",
) -> None:
    """Bar chart ranking all assets by a chosen metric."""
    df = pd.DataFrame([s for s in stats_list if s.get(metric) is not None])
    if df.empty:
        logger.warning(f"No data to plot for metric: {metric}")
        return
    df = df.sort_values(metric, ascending=False)

    fig, ax = plt.subplots(figsize=(max(10, len(df) * 0.55), 6))
    colors = ["#2ecc71" if v >= 0 else "#e74c3c" for v in df[metric]]
    bars = ax.barh(df["asset"], df[metric], color=colors, edgecolor="white")
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_xlabel(metric.replace("_", " ").title(), fontsize=10)
    ax.set_title(title, fontsize=13, fontweight="bold")
    ax.invert_yaxis()
    for bar, val in zip(bars, df[metric]):
        ax.text(
            bar.get_width() + (0.005 if val >= 0 else -0.005),
            bar.get_y() + bar.get_height() / 2,
            f"{val:.2f}", va="center", ha="left" if val >= 0 else "right", fontsize=7,
        )
    fig.tight_layout()
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(str(output_path), dpi=FIGURE_DPI, bbox_inches="tight")
    plt.close(fig)
    logger.info(f"Performance ranking saved → {output_path}")


# ─── Private Plot Helpers ─────────────────────────────────────────────────────

def _add_cover_page(pdf: PdfPages, category: str, asset_names: list) -> None:
    fig = plt.figure(figsize=(11, 8.5))
    fig.text(0.5, 0.65, f"FinNexus EDA Report", ha="center", fontsize=26, fontweight="bold")
    fig.text(0.5, 0.55, f"Category: {category}", ha="center", fontsize=18, color="#2c3e50")
    fig.text(0.5, 0.45, f"Assets: {', '.join(asset_names)}", ha="center", fontsize=10,
             color="#555", wrap=True)
    fig.text(0.5, 0.35, f"Generated by FinNexus Data Pipeline", ha="center", fontsize=9,
             color="#888")
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def _page_price_analysis(pdf: PdfPages, df: pd.DataFrame, name: str) -> None:
    dates = pd.to_datetime(df["Date"])
    close = df["Close"]

    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    fig.suptitle(f"{name} — Price Analysis", fontsize=14, fontweight="bold")

    # 1. Price history (linear)
    ax = axes[0, 0]
    ax.plot(dates, close, linewidth=1, color="#2980b9")
    ax.set_title("Price History (Linear)")
    ax.set_ylabel("Price")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.tick_params(axis="x", rotation=30)

    # 2. Price history (log)
    ax = axes[0, 1]
    ax.semilogy(dates, close, linewidth=1, color="#8e44ad")
    ax.set_title("Price History (Log Scale)")
    ax.set_ylabel("Price (log)")
    ax.tick_params(axis="x", rotation=30)

    # 3. Add SMA overlays if columns exist
    ax = axes[1, 0]
    ax.plot(dates, close, linewidth=0.8, label="Close", color="#2980b9", alpha=0.8)
    for sma, col in [("SMA20", "sma_20"), ("SMA50", "sma_50"), ("SMA200", "sma_200")]:
        if col in df.columns:
            ax.plot(dates, df[col], linewidth=0.9, label=sma, alpha=0.85)
    ax.set_title("Price + Moving Averages")
    ax.legend(fontsize=7)
    ax.tick_params(axis="x", rotation=30)

    # 4. Drawdown chart
    ax = axes[1, 1]
    daily_ret = close.pct_change()
    cum = (1 + daily_ret.fillna(0)).cumprod()
    peak = cum.expanding().max()
    dd = (cum - peak) / peak * 100
    ax.fill_between(dates, dd, 0, alpha=0.5, color="#e74c3c")
    ax.plot(dates, dd, linewidth=0.7, color="#c0392b")
    ax.set_title("Drawdown (%)")
    ax.set_ylabel("%")
    ax.tick_params(axis="x", rotation=30)

    fig.tight_layout()
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def _page_returns_analysis(pdf: PdfPages, df: pd.DataFrame, name: str) -> None:
    close = df["Close"]
    daily_ret = close.pct_change().dropna()

    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    fig.suptitle(f"{name} — Returns Analysis", fontsize=14, fontweight="bold")

    # 1. Returns histogram
    ax = axes[0, 0]
    ax.hist(daily_ret * 100, bins=60, color="#27ae60", edgecolor="white", alpha=0.8)
    ax.axvline(0, color="black", linewidth=1)
    ax.set_title("Daily Returns Distribution (%)")
    ax.set_xlabel("Daily Return (%)")

    # 2. Q-Q plot
    ax = axes[0, 1]
    from scipy import stats as scipy_stats
    osm, osr = scipy_stats.probplot(daily_ret.dropna(), dist="norm")
    ax.scatter(osm[0], osm[1], s=4, alpha=0.5, color="#2980b9")
    min_val, max_val = osm[0][0], osm[0][-1]
    ax.plot([min_val, max_val],
            [osr[1] + osr[0]*min_val, osr[1] + osr[0]*max_val],
            color="red", linewidth=1.5)
    ax.set_title("Q-Q Plot (Normality)")
    ax.set_xlabel("Theoretical Quantiles")
    ax.set_ylabel("Sample Quantiles")

    # 3. Rolling 30-day return
    ax = axes[1, 0]
    roll_ret = close.pct_change(30) * 100
    dates = pd.to_datetime(df["Date"])
    ax.plot(dates, roll_ret, linewidth=0.8, color="#e67e22")
    ax.axhline(0, color="black", linewidth=0.8)
    ax.fill_between(dates, roll_ret, 0,
                    where=(roll_ret >= 0), alpha=0.3, color="#2ecc71")
    ax.fill_between(dates, roll_ret, 0,
                    where=(roll_ret < 0), alpha=0.3, color="#e74c3c")
    ax.set_title("Rolling 30-Day Return (%)")
    ax.tick_params(axis="x", rotation=30)

    # 4. Rolling 7 / 30 / 90 day volatility
    ax = axes[1, 1]
    log_ret = np.log(close / close.shift(1))
    for w, col_c in [(7, "#3498db"), (30, "#e67e22"), (90, "#9b59b6")]:
        vol = log_ret.rolling(w).std() * np.sqrt(252) * 100
        ax.plot(dates, vol, linewidth=0.8, label=f"Vol {w}d", color=col_c, alpha=0.9)
    ax.set_title("Rolling Volatility (Annualised %)")
    ax.legend(fontsize=7)
    ax.tick_params(axis="x", rotation=30)

    fig.tight_layout()
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def _page_volume_analysis(pdf: PdfPages, df: pd.DataFrame, name: str) -> None:
    dates = pd.to_datetime(df["Date"])
    close = df["Close"]
    vol = df["Volume"].replace(0, np.nan)

    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    fig.suptitle(f"{name} — Volume Analysis", fontsize=14, fontweight="bold")

    # 1. Volume bar chart
    ax = axes[0, 0]
    ax.bar(dates, vol, width=1, color="#2980b9", alpha=0.6)
    vol_ma = vol.rolling(30).mean()
    ax.plot(dates, vol_ma, color="orange", linewidth=1.2, label="30d MA")
    ax.set_title("Daily Volume")
    ax.legend(fontsize=7)
    ax.tick_params(axis="x", rotation=30)

    # 2. Volume vs Price
    ax = axes[0, 1]
    ax2 = ax.twinx()
    ax.bar(dates, vol, width=1, color="#3498db", alpha=0.4, label="Volume")
    ax2.plot(dates, close, linewidth=0.9, color="#e74c3c", label="Close")
    ax.set_title("Volume vs Price")
    ax.set_ylabel("Volume", color="#3498db")
    ax2.set_ylabel("Price", color="#e74c3c")
    ax.tick_params(axis="x", rotation=30)

    # 3. Volume ratio (7d / 30d avg)
    ax = axes[1, 0]
    vol_ratio = vol.rolling(7).mean() / vol.rolling(30).mean()
    ax.plot(dates, vol_ratio, linewidth=0.8, color="#27ae60")
    ax.axhline(1.0, color="black", linewidth=0.8, linestyle="--")
    ax.axhline(2.0, color="red", linewidth=0.8, linestyle="--", label="2× spike")
    ax.set_title("Volume Ratio (7d avg / 30d avg)")
    ax.legend(fontsize=7)
    ax.tick_params(axis="x", rotation=30)

    # 4. OBV if present
    ax = axes[1, 1]
    if "obv" in df.columns:
        ax.plot(dates, df["obv"], linewidth=0.9, color="#8e44ad")
        ax.set_title("On-Balance Volume (OBV)")
    else:
        price_dir = np.sign(close.diff())
        obv = (price_dir * vol.fillna(0)).cumsum()
        ax.plot(dates, obv, linewidth=0.9, color="#8e44ad")
        ax.set_title("On-Balance Volume (OBV)")
    ax.tick_params(axis="x", rotation=30)

    fig.tight_layout()
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def _page_volatility_analysis(pdf: PdfPages, df: pd.DataFrame, name: str) -> None:
    dates = pd.to_datetime(df["Date"])
    close = df["Close"]
    log_ret = np.log(close / close.shift(1))

    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    fig.suptitle(f"{name} — Volatility Analysis", fontsize=14, fontweight="bold")

    # 1. Rolling vol 30d
    ax = axes[0, 0]
    vol30 = log_ret.rolling(30).std() * np.sqrt(252) * 100
    ax.plot(dates, vol30, linewidth=0.9, color="#e74c3c")
    ax.fill_between(dates, vol30, alpha=0.3, color="#e74c3c")
    ax.set_title("Annualised Volatility (30d Rolling) %")
    ax.tick_params(axis="x", rotation=30)

    # 2. Volatility clustering
    ax = axes[0, 1]
    ax.scatter(dates, log_ret.abs() * 100, s=2, alpha=0.4, color="#2980b9")
    ax.set_title("|Daily Log Return| — Volatility Clustering")
    ax.set_ylabel("| Log Return | (%)")
    ax.tick_params(axis="x", rotation=30)

    # 3. Bollinger bands
    ax = axes[1, 0]
    mid = close.rolling(20).mean()
    std = close.rolling(20).std()
    ax.plot(dates, close, linewidth=0.8, label="Close", color="#2980b9")
    ax.plot(dates, mid, linewidth=0.8, label="SMA20", color="orange", alpha=0.8)
    ax.fill_between(dates, mid - 2*std, mid + 2*std, alpha=0.2, color="orange",
                    label="BB ±2σ")
    ax.set_title("Bollinger Bands (20, ±2σ)")
    ax.legend(fontsize=7)
    ax.tick_params(axis="x", rotation=30)

    # 4. High/Low daily range
    ax = axes[1, 1]
    day_range_pct = (df["High"] - df["Low"]) / close * 100
    ax.plot(dates, day_range_pct.rolling(14).mean(), linewidth=0.9, color="#27ae60")
    ax.set_title("Daily Range % (High-Low / Close) — 14d MA")
    ax.set_ylabel("%")
    ax.tick_params(axis="x", rotation=30)

    fig.tight_layout()
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def _page_risk_metrics(
    pdf: PdfPages, df: pd.DataFrame, name: str, stats: dict
) -> None:
    fig = plt.figure(figsize=(11, 7))
    fig.suptitle(f"{name} — Risk Metrics Summary", fontsize=14, fontweight="bold")
    ax = fig.add_subplot(111)
    ax.axis("off")

    metrics = [
        ("Metric", "Value"),
        ("Total Return", f"{stats.get('total_return_pct', 'N/A')} %"),
        ("Annual Return", f"{stats.get('annual_return_pct', 'N/A')} %"),
        ("Ann. Volatility", f"{stats.get('ann_volatility', 'N/A')}"),
        ("Sharpe Ratio", f"{stats.get('sharpe_ratio', 'N/A')}"),
        ("Sortino Ratio", f"{stats.get('sortino_ratio', 'N/A')}"),
        ("Calmar Ratio", f"{stats.get('calmar_ratio', 'N/A')}"),
        ("Max Drawdown", f"{stats.get('max_drawdown_pct', 'N/A')} %"),
        ("VaR 95%", f"{stats.get('var_95_pct', 'N/A')} %"),
        ("Skewness", f"{stats.get('skewness', 'N/A')}"),
        ("Kurtosis (excess)", f"{stats.get('kurtosis', 'N/A')}"),
        ("Data Points", f"{stats.get('n_rows', 'N/A')}"),
    ]
    table = ax.table(
        cellText=metrics[1:],
        colLabels=metrics[0],
        loc="center",
        cellLoc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1.4, 1.7)
    for (r, c), cell in table.get_celld().items():
        if r == 0:
            cell.set_facecolor("#2c3e50")
            cell.set_text_props(color="white", fontweight="bold")
        elif r % 2 == 0:
            cell.set_facecolor("#ecf0f1")

    fig.tight_layout()
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)
