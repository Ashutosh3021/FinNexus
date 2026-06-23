"""
US ETF Data Collection Script
Primary source: yfinance (auto_adjust=True).
Falls back to pandas_datareader (Yahoo) if yfinance returns empty.
Fixes multi-level column header issue introduced in yfinance ≥0.2.
"""

import os
import sys
import subprocess
import time
import logging
import warnings
from datetime import datetime

warnings.filterwarnings('ignore')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def _pip_install(package):
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--quiet', package])


for _pkg in ['pandas', 'numpy', 'tqdm', 'yfinance', 'pandas-datareader']:
    try:
        __import__(_pkg.replace('-', '_'))
    except ImportError:
        logger.info(f"Installing {_pkg}…")
        _pip_install(_pkg)

import pandas as pd
import numpy as np
from tqdm import tqdm
import yfinance as yf


# pandas_datareader is optional – graceful fallback
try:
    import pandas_datareader.data as pdr_data
    _PDR_AVAILABLE = True
except Exception:
    _PDR_AVAILABLE = False
    logger.warning("pandas_datareader not available; will use yfinance only")


OHLCV = ['Open', 'High', 'Low', 'Close', 'Volume']


def _flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Collapse yfinance MultiIndex columns to simple strings."""
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df


def _standardise(df: pd.DataFrame) -> pd.DataFrame:
    """Rename columns to Open/High/Low/Close/Volume regardless of source."""
    if df is None or df.empty:
        return pd.DataFrame()
    df = _flatten_columns(df.copy())
    lower_map = {c.lower(): c for c in df.columns}
    rename = {}
    for want in OHLCV:
        if want not in df.columns and want.lower() in lower_map:
            rename[lower_map[want.lower()]] = want
    if rename:
        df.rename(columns=rename, inplace=True)
    present = [c for c in OHLCV if c in df.columns]
    if 'Close' not in present:
        return pd.DataFrame()
    if 'Volume' not in present:
        df['Volume'] = 0
    for c in ['Open', 'High', 'Low']:
        if c not in df.columns:
            df[c] = df['Close']
    df.index = pd.to_datetime(df.index).tz_localize(None)
    df.index.name = 'Date'
    return df[OHLCV].sort_index()


class USETFDataCollector:
    ETFS = {
        'SPY':  {'name': 'SPDR S&P 500 ETF',                                'category': 'Large Cap'},
        'QQQ':  {'name': 'Invesco QQQ Trust',                               'category': 'Large Cap'},
        'IVV':  {'name': 'iShares Core S&P 500 ETF',                        'category': 'Large Cap'},
        'XLK':  {'name': 'Technology Select Sector SPDR',                   'category': 'Sector'},
        'XLE':  {'name': 'Energy Select Sector SPDR',                       'category': 'Sector'},
        'XLV':  {'name': 'Health Care Select Sector SPDR',                  'category': 'Sector'},
        'AGG':  {'name': 'iShares Core U.S. Aggregate Bond ETF',            'category': 'Fixed Income'},
        'LQD':  {'name': 'iShares iBoxx IG Corporate Bond ETF',             'category': 'Fixed Income'},
        'TLT':  {'name': 'iShares 20+ Year Treasury Bond ETF',              'category': 'Fixed Income'},
        'GLD':  {'name': 'SPDR Gold Shares',                                'category': 'Commodity'},
        'USO':  {'name': 'United States Oil Fund',                          'category': 'Commodity'},
        'EFA':  {'name': 'iShares MSCI EAFE ETF',                           'category': 'International'},
        'EEM':  {'name': 'iShares MSCI Emerging Markets ETF',               'category': 'International'},
        'EWY':  {'name': 'iShares MSCI South Korea ETF',                    'category': 'International'},
        'IBIT': {'name': 'iShares Bitcoin Trust',                           'category': 'Alternatives'},
    }

    # IBIT only listed Jan 2024; lower the bar for it
    LOW_COVERAGE_TICKERS = {'IBIT'}

    def __init__(self, start_date='2021-01-01', end_date=None, output_dir='ETF'):
        self.start_date = datetime.strptime(start_date, '%Y-%m-%d')
        self.end_date = datetime.strptime(
            end_date or datetime.today().strftime('%Y-%m-%d'), '%Y-%m-%d')
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        logger.info(f"ETF collector ready  ·  {len(self.ETFS)} ETFs  ·  "
                    f"{self.start_date.date()} → {self.end_date.date()}")

    # ------------------------------------------------------------------
    # yfinance
    # ------------------------------------------------------------------
    def _yfinance(self, symbol: str) -> pd.DataFrame:
        try:
            raw = yf.download(symbol, start=self.start_date, end=self.end_date,
                              progress=False, auto_adjust=True)
            return _standardise(raw)
        except Exception as e:
            logger.debug(f"yfinance failed for {symbol}: {e}")
            return pd.DataFrame()

    # ------------------------------------------------------------------
    # pandas_datareader (Yahoo)
    # ------------------------------------------------------------------
    def _pdr(self, symbol: str) -> pd.DataFrame:
        if not _PDR_AVAILABLE:
            return pd.DataFrame()
        try:
            raw = pdr_data.DataReader(symbol, 'yahoo', self.start_date, self.end_date)
            return _standardise(raw)
        except Exception as e:
            logger.debug(f"pdr failed for {symbol}: {e}")
            return pd.DataFrame()

    # ------------------------------------------------------------------
    # Combine
    # ------------------------------------------------------------------
    def _collect_one(self, symbol: str) -> pd.DataFrame:
        frames, used = [], []

        df = self._yfinance(symbol)
        if not df.empty:
            frames.append(df); used.append('yfinance')

        if not frames:                  # only try pdr if yfinance failed entirely
            df = self._pdr(symbol)
            if not df.empty:
                frames.append(df); used.append('pdr')

        if not frames:
            return pd.DataFrame()

        combined = frames[0]
        for extra in frames[1:]:
            combined = combined.combine_first(extra)
        combined = combined[~combined.index.duplicated(keep='last')].sort_index()
        logger.debug(f"{symbol}: {len(combined)} rows  [{', '.join(used)}]")
        return combined

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------
    def _validate(self, symbol: str, df: pd.DataFrame) -> bool:
        if df.empty:
            return False
        expected = (self.end_date - self.start_date).days
        coverage = len(df) / expected
        threshold = 0.20 if symbol in self.LOW_COVERAGE_TICKERS else 0.55
        if coverage < threshold:
            logger.warning(f"Low coverage for {symbol}: {coverage:.1%}")
            return False
        if df['Close'].std(ddof=0) == 0:
            logger.warning(f"Zero variance for {symbol}")
            return False
        return True

    # ------------------------------------------------------------------
    # Persist
    # ------------------------------------------------------------------
    def _save(self, symbol: str, df: pd.DataFrame, info: dict):
        path = os.path.join(self.output_dir, f"{symbol}.csv")
        df.sort_index().to_csv(path)

        meta = {
            'symbol': symbol, 'name': info['name'], 'category': info['category'],
            'start_date': self.start_date.strftime('%Y-%m-%d'),
            'end_date': self.end_date.strftime('%Y-%m-%d'),
            'interval': '1 Day', 'total_rows': len(df),
            'actual_start': df.index.min().strftime('%Y-%m-%d'),
            'actual_end': df.index.max().strftime('%Y-%m-%d'),
            'data_completeness': f"{len(df) / (self.end_date - self.start_date).days:.1%}",
        }
        pd.DataFrame([meta]).to_csv(
            os.path.join(self.output_dir, f"{symbol}_metadata.csv"), index=False)

    def _save_master(self, results: dict, failed: list):
        rows = []
        for sym, info in self.ETFS.items():
            rows.append({
                'symbol': sym, 'name': info['name'], 'category': info['category'],
                'status': 'Success' if sym in results else 'Failed',
                'rows': len(results[sym]) if sym in results else 0,
                'start_date': self.start_date.strftime('%Y-%m-%d'),
                'end_date': self.end_date.strftime('%Y-%m-%d'),
            })
        pd.DataFrame(rows).to_csv(
            os.path.join(self.output_dir, 'MASTER_SUMMARY.csv'), index=False)
        logger.info(f"✓ Saved master summary → {self.output_dir}/MASTER_SUMMARY.csv")

    # ------------------------------------------------------------------
    # Main
    # ------------------------------------------------------------------
    def collect_all(self):
        logger.info("=" * 60)
        logger.info("US ETF DATA COLLECTION")
        logger.info(f"Date range : {self.start_date.date()} → {self.end_date.date()}")
        logger.info(f"Output dir : {self.output_dir}  ·  {len(self.ETFS)} ETFs")
        logger.info("=" * 60)

        results, failed = {}, []

        for symbol, info in tqdm(self.ETFS.items(), desc="Collecting ETFs"):
            logger.info(f"Collecting {symbol} ({info['name']})")
            try:
                df = self._collect_one(symbol)
                if self._validate(symbol, df):
                    self._save(symbol, df, info)
                    results[symbol] = df
                    logger.info(f"  ✓ {symbol}: {len(df)} rows saved")
                else:
                    logger.warning(f"  ✗ Validation failed for {symbol}")
                    failed.append(symbol)
            except Exception as e:
                logger.error(f"  ✗ Error for {symbol}: {e}")
                failed.append(symbol)
            time.sleep(0.5)

        self._save_master(results, failed)

        logger.info("\n" + "=" * 60)
        logger.info("DATA COLLECTION COMPLETE!")
        logger.info(f"✓ Collected : {len(results)}/{len(self.ETFS)} ETFs")
        if failed:
            logger.warning(f"✗ Failed    : {', '.join(failed)}")
        logger.info("=" * 60)

        # Quality report
        logger.info("\nDATA QUALITY REPORT")
        logger.info("=" * 60)
        for sym, info in self.ETFS.items():
            fp = os.path.join(self.output_dir, f"{sym}.csv")
            if os.path.exists(fp):
                d = pd.read_csv(fp, index_col=0, parse_dates=True)
                cov = len(d) / (self.end_date - self.start_date).days * 100
                logger.info(f"  {sym}: {len(d):,} rows  |  {cov:.1f}% coverage  "
                            f"|  {d.index.min().date()} → {d.index.max().date()}")
            else:
                logger.warning(f"  {sym}: file not found")

        return results, failed


def main():
    collector = USETFDataCollector(
        start_date='2021-01-01',
        end_date=datetime.today().strftime('%Y-%m-%d'),
        output_dir='ETF',
    )
    collector.collect_all()


if __name__ == '__main__':
    main()
