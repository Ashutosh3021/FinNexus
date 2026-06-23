"""
Commodity Data Collection Script
Sources used (in priority order):
  1. yfinance  — ETF/futures proxies freely available for most commodities
  2. EODHD     — if EODHD_API_KEY env var is set
  3. OilPrice  — if OILPRICEAPI_KEY env var is set (energy only)

Every commodity has at least one yfinance ticker so the script works
with zero API keys while API-sourced data is used to supplement when
available.
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


for _pkg in ['pandas', 'numpy', 'tqdm', 'yfinance', 'requests', 'python-dotenv']:
    try:
        __import__(_pkg.replace('-', '_'))
    except ImportError:
        logger.info(f"Installing {_pkg}…")
        _pip_install(_pkg)

import pandas as pd
import numpy as np
import requests
from tqdm import tqdm
import yfinance as yf
from dotenv import load_dotenv

load_dotenv()

OHLCV = ['Open', 'High', 'Low', 'Close', 'Volume']


def _flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df


def _standardise(df: pd.DataFrame, price_col: str = 'Close') -> pd.DataFrame:
    """Ensure OHLCV columns are present and index is DatetimeIndex named 'Date'."""
    if df is None or df.empty:
        return pd.DataFrame()
    df = _flatten_columns(df.copy())
    # Case-insensitive rename
    lmap = {c.lower(): c for c in df.columns}
    rename = {}
    for want in OHLCV:
        if want not in df.columns and want.lower() in lmap:
            rename[lmap[want.lower()]] = want
    if rename:
        df.rename(columns=rename, inplace=True)

    # If only a single price column exists, create synthetic OHLC
    if 'Close' not in df.columns:
        for candidate in [price_col, 'Price', 'Value', 'price', 'value']:
            if candidate in df.columns:
                df['Close'] = df[candidate]
                break
    if 'Close' not in df.columns:
        return pd.DataFrame()

    for c in ['Open', 'High', 'Low']:
        if c not in df.columns:
            df[c] = df['Close']
    if 'Volume' not in df.columns:
        df['Volume'] = 0

    df.index = pd.to_datetime(df.index).tz_localize(None)
    df.index.name = 'Date'
    return df[OHLCV].sort_index()


# ---------------------------------------------------------------------------
# Commodity definitions
# yf_tickers: list of yfinance symbols to try in order (first success wins)
# ---------------------------------------------------------------------------
COMMODITIES = {
    'Energy': {
        'Brent_Crude_Oil': {
            'yf_tickers': ['BZ=F', 'BNO'],           # Brent futures / Brent ETF
            'eodhd_code': 'BRENT.COMM',
        },
        'WTI_Crude_Oil': {
            'yf_tickers': ['CL=F', 'USO'],            # WTI futures / US Oil ETF
            'eodhd_code': 'WTI.COMM',
        },
        'Natural_Gas': {
            'yf_tickers': ['NG=F', 'UNG'],            # Nat gas futures / ETF
            'eodhd_code': 'NATURALGAS.COMM',
        },
    },
    'Precious_Metals': {
        'Gold': {
            'yf_tickers': ['GC=F', 'GLD', 'IAU'],    # Gold futures / ETFs
            'eodhd_code': 'XAUUSD.FOREX',
        },
        'Silver': {
            'yf_tickers': ['SI=F', 'SLV'],
            'eodhd_code': 'XAGUSD.FOREX',
        },
        'Platinum': {
            'yf_tickers': ['PL=F', 'PPLT'],
            'eodhd_code': None,
        },
    },
    'Base_Metals': {
        'Copper': {
            'yf_tickers': ['HG=F', 'CPER'],          # Copper futures / ETF
            'eodhd_code': None,
        },
        'Aluminum': {
            'yf_tickers': ['ALI=F'],                  # Aluminum futures
            'eodhd_code': None,
        },
        'Lead': {
            'yf_tickers': ['LL=F'],                   # Lead futures
            'eodhd_code': None,
        },
    },
    'Agriculture': {
        'Wheat': {
            'yf_tickers': ['ZW=F', 'WEAT'],          # Wheat futures / ETF
            'eodhd_code': None,
        },
        'Corn': {
            'yf_tickers': ['ZC=F', 'CORN'],          # Corn futures / ETF
            'eodhd_code': None,
        },
        'Cotton': {
            'yf_tickers': ['CT=F', 'BAL'],           # Cotton futures / ETF
            'eodhd_code': None,
        },
        'Natural_Rubber': {
            'yf_tickers': ['CEAT.NS', 'MRF.NS', 'APOLLOTYRE.NS'],  # Indian tyre cos = rubber price proxies
            'eodhd_code': None,
        },
    },
    'Fertilizers': {
        'Fertilizer_Index': {
            'yf_tickers': ['MOO', 'MOS', 'NTR'],     # Agri / fertiliser proxies
            'eodhd_code': None,
        },
    },
}


class CommodityDataCollector:
    def __init__(self, start_date='2021-01-01', end_date=None, output_dir='Commodities'):
        self.start_date = datetime.strptime(start_date, '%Y-%m-%d')
        self.end_date = datetime.strptime(
            end_date or datetime.today().strftime('%Y-%m-%d'), '%Y-%m-%d')
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        self.eodhd_key = os.getenv('EODHD_API_KEY')
        if not self.eodhd_key:
            logger.warning("EODHD_API_KEY not set – skipping EODHD source")

        logger.info(f"Commodity collector ready  ·  "
                    f"{self.start_date.date()} → {self.end_date.date()}")

    # ------------------------------------------------------------------
    # yfinance
    # ------------------------------------------------------------------
    def _yfinance(self, tickers: list) -> pd.DataFrame:
        for sym in tickers:
            try:
                raw = yf.download(sym, start=self.start_date, end=self.end_date,
                                  progress=False, auto_adjust=True)
                df = _standardise(raw)
                if not df.empty and len(df) >= 10:
                    logger.debug(f"  yfinance {sym}: {len(df)} rows")
                    return df
            except Exception as e:
                logger.debug(f"  yfinance {sym} failed: {e}")
        return pd.DataFrame()

    # ------------------------------------------------------------------
    # EODHD
    # ------------------------------------------------------------------
    def _eodhd(self, code: str) -> pd.DataFrame:
        if not self.eodhd_key or not code:
            return pd.DataFrame()
        try:
            url = f"https://eodhd.com/api/eod/{code}"
            params = {
                'api_token': self.eodhd_key,
                'fmt': 'json',
                'from': self.start_date.strftime('%Y-%m-%d'),
                'to': self.end_date.strftime('%Y-%m-%d'),
            }
            r = requests.get(url, params=params, timeout=15)
            if r.status_code != 200:
                return pd.DataFrame()
            data = r.json()
            if not isinstance(data, list) or len(data) == 0:
                return pd.DataFrame()
            df = pd.DataFrame(data)
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            df.rename(columns={'open': 'Open', 'high': 'High',
                               'low': 'Low', 'close': 'Close',
                               'volume': 'Volume'}, inplace=True)
            df = _standardise(df)
            logger.debug(f"  EODHD {code}: {len(df)} rows")
            return df
        except Exception as e:
            logger.debug(f"  EODHD {code} failed: {e}")
            return pd.DataFrame()

    # ------------------------------------------------------------------
    # Combine
    # ------------------------------------------------------------------
    def _collect_one(self, name: str, info: dict) -> pd.DataFrame:
        frames, used = [], []

        # yfinance first (no API key needed)
        df = self._yfinance(info.get('yf_tickers', []))
        if not df.empty:
            frames.append(df); used.append('yfinance')

        # EODHD to fill gaps
        if info.get('eodhd_code'):
            df = self._eodhd(info['eodhd_code'])
            if not df.empty:
                frames.append(df); used.append('EODHD')

        if not frames:
            return pd.DataFrame()

        combined = frames[0]
        for extra in frames[1:]:
            combined = combined.combine_first(extra)
        combined = combined[~combined.index.duplicated(keep='last')].sort_index()
        logger.info(f"✓ {name}: {len(combined)} rows  [{', '.join(used)}]")
        return combined

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------
    def _save_master(self, results: dict, failed: list):
        rows = []
        for cat, items in COMMODITIES.items():
            for name in items:
                rows.append({
                    'category': cat, 'commodity': name,
                    'status': 'Success' if name in results else 'Failed',
                    'rows': len(results[name]) if name in results else 0,
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
        logger.info("COMMODITY DATA COLLECTION")
        logger.info(f"Date range : {self.start_date.date()} → {self.end_date.date()}")
        logger.info(f"Output dir : {self.output_dir}")
        logger.info("=" * 60)

        results, failed = {}, []
        total = sum(len(v) for v in COMMODITIES.values())

        for category, items in COMMODITIES.items():
            logger.info(f"\n📁 Category: {category}")
            for name, info in tqdm(items.items(), desc=category):
                try:
                    df = self._collect_one(name, info)
                    if not df.empty:
                        path = os.path.join(self.output_dir, f"{name}.csv")
                        df.to_csv(path)
                        logger.info(f"  ✓ Saved {name} → {path}  ({len(df)} rows)")
                        results[name] = df
                    else:
                        logger.warning(f"  ✗ No data for {name}")
                        failed.append(name)
                except Exception as e:
                    logger.error(f"  Error for {name}: {e}")
                    failed.append(name)
                time.sleep(0.5)

        self._save_master(results, failed)

        logger.info("\n" + "=" * 60)
        logger.info("DATA COLLECTION COMPLETE!")
        logger.info(f"✓ Collected : {len(results)}/{total} commodities")
        if failed:
            logger.warning(f"✗ Failed    : {', '.join(failed)}")
        logger.info("=" * 60)
        return results, failed


def main():
    collector = CommodityDataCollector(
        start_date='2021-01-01',
        end_date=datetime.today().strftime('%Y-%m-%d'),
        output_dir='Commodities',
    )
    collector.collect_all()


if __name__ == '__main__':
    main()
