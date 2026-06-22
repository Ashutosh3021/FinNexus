"""
Cryptocurrency Data Collection Script
Uses CCXT (Binance) as primary, yfinance as fallback.
CoinGecko OHLC endpoint requires a paid API key, so it is skipped.
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
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", package])


for _pkg in ['pandas', 'numpy', 'tqdm', 'ccxt', 'yfinance']:
    try:
        __import__(_pkg)
    except ImportError:
        logger.info(f"Installing {_pkg}…")
        _pip_install(_pkg)

import pandas as pd
import numpy as np
from tqdm import tqdm
import ccxt
import yfinance as yf


class CryptoDataCollector:
    CRYPTOS = {
        'Bitcoin':     {'symbol': 'BTC',  'ccxt': 'BTC/USDT',  'yf': 'BTC-USD',  'category': 'Store of Value'},
        'Ethereum':    {'symbol': 'ETH',  'ccxt': 'ETH/USDT',  'yf': 'ETH-USD',  'category': 'Smart Contract'},
        'Solana':      {'symbol': 'SOL',  'ccxt': 'SOL/USDT',  'yf': 'SOL-USD',  'category': 'Smart Contract'},
        'BNB':         {'symbol': 'BNB',  'ccxt': 'BNB/USDT',  'yf': 'BNB-USD',  'category': 'Exchange/Utility'},
        'TRON':        {'symbol': 'TRX',  'ccxt': 'TRX/USDT',  'yf': 'TRX-USD',  'category': 'Payments/Stable'},
        'Monero':      {'symbol': 'XMR',  'ccxt': 'XMR/USDT',  'yf': 'XMR-USD',  'category': 'Privacy'},
        'Litecoin':    {'symbol': 'LTC',  'ccxt': 'LTC/USDT',  'yf': 'LTC-USD',  'category': 'Payments'},
        'Hyperliquid': {'symbol': 'HYPE', 'ccxt': 'HYPE/USDT', 'yf': None,        'category': 'DeFi/Perps'},
        'Uniswap':     {'symbol': 'UNI',  'ccxt': 'UNI/USDT',  'yf': 'UNI-USD',  'category': 'DeFi/Exchange'},
        'Worldcoin':   {'symbol': 'WLD',  'ccxt': 'WLD/USDT',  'yf': None,        'category': 'AI'},
    }

    def __init__(self, start_date='2024-01-01', end_date=None, output_dir='Crypto'):
        self.start_date = datetime.strptime(start_date, '%Y-%m-%d')
        self.end_date = datetime.strptime(end_date or datetime.today().strftime('%Y-%m-%d'), '%Y-%m-%d')
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        self.exchange = None
        try:
            self.exchange = ccxt.binance({'enableRateLimit': True})
            self.exchange.load_markets()
            logger.info("✓ CCXT (Binance) initialised")
        except Exception as e:
            logger.warning(f"CCXT init failed: {e}")

        logger.info(f"Collector ready  ·  {len(self.CRYPTOS)} coins  ·  "
                    f"{self.start_date.date()} → {self.end_date.date()}")

    # ------------------------------------------------------------------
    # CCXT fetch (handles >1000-row pagination automatically)
    # ------------------------------------------------------------------
    def _ccxt(self, info: dict) -> pd.DataFrame:
        if not self.exchange:
            return pd.DataFrame()
        sym = info['ccxt']
        if sym not in self.exchange.markets:
            return pd.DataFrame()
        try:
            since = int(self.start_date.timestamp() * 1000)
            rows = []
            while True:
                batch = self.exchange.fetch_ohlcv(sym, '1d', since=since, limit=1000)
                if not batch:
                    break
                rows.extend(batch)
                if len(batch) < 1000:
                    break
                since = batch[-1][0] + 86_400_000   # next day in ms
                time.sleep(self.exchange.rateLimit / 1000)

            if not rows:
                return pd.DataFrame()

            df = pd.DataFrame(rows, columns=['ts', 'Open', 'High', 'Low', 'Close', 'Volume'])
            df['Date'] = pd.to_datetime(df['ts'], unit='ms', utc=True).dt.tz_localize(None)
            df.set_index('Date', inplace=True)
            df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
            mask = (df.index >= self.start_date) & (df.index <= self.end_date)
            return df.loc[mask].sort_index()
        except Exception as e:
            logger.debug(f"CCXT failed for {sym}: {e}")
            return pd.DataFrame()

    # ------------------------------------------------------------------
    # yfinance fetch  (handles multi-level columns from v0.2+)
    # ------------------------------------------------------------------
    def _yfinance(self, info: dict) -> pd.DataFrame:
        sym = info.get('yf')
        if not sym:
            return pd.DataFrame()
        try:
            raw = yf.download(sym, start=self.start_date, end=self.end_date,
                              progress=False, auto_adjust=True)
            if raw is None or raw.empty:
                return pd.DataFrame()

            # yfinance ≥0.2 may return MultiIndex columns like ('Close','BTC-USD')
            if isinstance(raw.columns, pd.MultiIndex):
                raw.columns = raw.columns.get_level_values(0)

            cols = {c.lower(): c for c in raw.columns}
            rename = {}
            for want in ['Open', 'High', 'Low', 'Close', 'Volume']:
                if want in raw.columns:
                    pass
                elif want.lower() in cols:
                    rename[cols[want.lower()]] = want
            if rename:
                raw.rename(columns=rename, inplace=True)

            needed = [c for c in ['Open', 'High', 'Low', 'Close', 'Volume'] if c in raw.columns]
            df = raw[needed].copy()
            df.index = pd.to_datetime(df.index).tz_localize(None)
            df.index.name = 'Date'
            return df.sort_index()
        except Exception as e:
            logger.debug(f"yfinance failed for {sym}: {e}")
            return pd.DataFrame()

    # ------------------------------------------------------------------
    # Combine sources
    # ------------------------------------------------------------------
    def _collect_one(self, name: str, info: dict) -> pd.DataFrame:
        frames, used = [], []

        df = self._ccxt(info)
        if not df.empty:
            frames.append(df); used.append('CCXT')

        df = self._yfinance(info)
        if not df.empty:
            frames.append(df); used.append('yfinance')

        if not frames:
            return pd.DataFrame()

        combined = frames[0]
        for extra in frames[1:]:
            combined = combined.combine_first(extra)
        combined = combined[~combined.index.duplicated(keep='last')].sort_index()

        logger.info(f"✓ {name}: {len(combined)} rows from {', '.join(used)}")
        return combined

    # ------------------------------------------------------------------
    # Save helpers
    # ------------------------------------------------------------------
    def _save_metadata(self, name: str, info: dict, df: pd.DataFrame):
        meta = {
            'name': name, 'symbol': info['symbol'], 'category': info['category'],
            'ccxt_symbol': info['ccxt'], 'yf_symbol': info.get('yf', 'N/A'),
            'start_date': self.start_date.strftime('%Y-%m-%d'),
            'end_date': self.end_date.strftime('%Y-%m-%d'),
            'interval': '1 Day', 'total_rows': len(df),
            'actual_start': df.index.min().strftime('%Y-%m-%d'),
            'actual_end': df.index.max().strftime('%Y-%m-%d'),
        }
        pd.DataFrame([meta]).to_csv(
            os.path.join(self.output_dir, f"{info['symbol']}_metadata.csv"), index=False)

    def _save_master(self, results: dict):
        rows = []
        for name, info in self.CRYPTOS.items():
            sym = info['symbol']
            rows.append({
                'name': name, 'symbol': sym, 'category': info['category'],
                'status': 'Success' if sym in results else 'Failed',
                'rows': len(results[sym]) if sym in results else 0,
                'start_date': self.start_date.strftime('%Y-%m-%d'),
                'end_date': self.end_date.strftime('%Y-%m-%d'),
            })
        pd.DataFrame(rows).to_csv(
            os.path.join(self.output_dir, 'MASTER_SUMMARY.csv'), index=False)
        logger.info(f"✓ Saved master summary → {self.output_dir}/MASTER_SUMMARY.csv")

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------
    def collect_all(self):
        logger.info("=" * 60)
        logger.info("CRYPTOCURRENCY DATA COLLECTION")
        logger.info(f"Date range : {self.start_date.date()} → {self.end_date.date()}")
        logger.info(f"Output dir : {self.output_dir}")
        logger.info("=" * 60)

        results, failed = {}, []

        for name, info in tqdm(self.CRYPTOS.items(), desc="Collecting Crypto Data"):
            logger.info(f"\n📊 {name} ({info['symbol']}) — {info['category']}")
            try:
                df = self._collect_one(name, info)
                if not df.empty:
                    sym = info['symbol']
                    path = os.path.join(self.output_dir, f"{sym}.csv")
                    df.to_csv(path)
                    logger.info(f"  ✓ Saved → {path}  ({len(df)} rows)")
                    results[sym] = df
                    self._save_metadata(name, info, df)
                else:
                    logger.warning(f"  ✗ No data for {name}")
                    failed.append(info['symbol'])
            except Exception as e:
                logger.error(f"Error processing {name}: {e}")
                failed.append(info['symbol'])
            time.sleep(1)

        self._save_master(results)

        logger.info("\n" + "=" * 60)
        logger.info("DATA COLLECTION COMPLETE!")
        logger.info(f"✓ Collected : {len(results)}/{len(self.CRYPTOS)}")
        if failed:
            logger.warning(f"✗ Failed    : {', '.join(failed)}")
        logger.info("=" * 60)
        return results, failed


def main():
    collector = CryptoDataCollector(
        start_date='2024-01-01',
        end_date=datetime.today().strftime('%Y-%m-%d'),
        output_dir='Crypto',
    )
    collector.collect_all()


if __name__ == '__main__':
    main()
