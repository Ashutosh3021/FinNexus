"""
Targeted re-collect for all previously failed symbols.
Reads existing CSVs, skips symbols that already have good data,
only downloads what's missing/failed. Merges into existing index CSVs.
"""

import os
import sys
import subprocess
import time
import logging
import warnings
from datetime import datetime, timedelta
from typing import Dict, List, Optional

warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def _pip(pkg):
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--quiet', pkg])


for _p in ['yfinance', 'pandas', 'tqdm']:
    try:
        __import__(_p)
    except ImportError:
        _pip(_p)

import pandas as pd
import yfinance as yf
from tqdm import tqdm

# ── date range ──────────────────────────────────────────────────────────────
START = datetime(2021, 1, 1)
END   = datetime.today()
OHLCV = ['Open', 'High', 'Low', 'Close', 'Volume']

# ── symbol alias map (confirmed working June 2026) ──────────────────────────
ALIASES: Dict[str, List[str]] = {
    # N50
    'TATAMOTORS':  ['TATAMOTORS.NS', '532755.BO'],
    # NNext
    'MCDOWELL-N':  ['UNITDSPR.NS'],
    # NMidcap
    'EQUITAS':     ['EQUITASBNK.NS'],
    'LTIM':        ['540005.BO'],
    'MGLEM':       ['MGL.NS'],
    'PRINCEPIPES': ['PRINCEPIPE.NS'],
    'SAILCORP':    ['SAIL.NS'],
    'SUVENPHAR':   ['SUVEN.NS'],
    'TCNSBRANDS':  [],                            # delisted (ABFRL buyout) — skip
    'WABCOINDIA':  ['533023.BO', 'ZFCVINDIA.NS'],
    'ZOMATO':      ['ETERNAL.NS'],
    'JUBILANT':    ['JUBLFOOD.NS'],
    # NSmallcap
    'AEGISCHEM':   ['AEGISLOG.NS'],
    'AKZOINDIA':   ['500710.BO'],
    'AMARAJABAT':  ['500008.BO'],
    'BARBEQUE':    ['SAPPHIRE.NS'],
    'COSMOFILM':   ['COSMOFIRST.NS'],
    'DCB':         ['DCBBANK.NS'],
    'DELCYCLES':   ['HERCULES.NS'],
    'DHANI':       [],                            # delisted — skip
    'DPWWORLD':    ['GPPL.NS'],
    'EUROBONDS':   ['EUROBOND.NS'],
    'FLEX':        ['FLEX.BO', 'FLEXINDUSTRI.NS', 'FLEXI.NS'],  # Flex Industries
    'GMR':         ['GMRINFRA.NS', 'GMRAIRPORT.NS', 'GMR.BO'],  # GMR Airports Infrastructure
    # N50 timeout retries
    'BAJFINANCE':  ['BAJFINANCE.NS'],
    'BPCL':        ['BPCL.NS'],
    'EICHERMOT':   ['EICHERMOT.NS'],
}

# which index CSV each symbol belongs to
SYMBOL_INDEX: Dict[str, str] = {
    'TATAMOTORS': 'N50',   'BAJFINANCE': 'N50',
    'BPCL':       'N50',   'EICHERMOT':  'N50',
    'MCDOWELL-N': 'NNext',
    'EQUITAS':    'NMidcap', 'LTIM':       'NMidcap',
    'MGLEM':      'NMidcap', 'PRINCEPIPES':'NMidcap',
    'SAILCORP':   'NMidcap', 'SUVENPHAR':  'NMidcap',
    'TCNSBRANDS': 'NMidcap', 'WABCOINDIA': 'NMidcap',
    'ZOMATO':     'NMidcap', 'JUBILANT':   'NMidcap',
    'AEGISCHEM':  'NSmallcap','AKZOINDIA':  'NSmallcap',
    'AMARAJABAT': 'NSmallcap','BARBEQUE':   'NSmallcap',
    'COSMOFILM':  'NSmallcap','DCB':        'NSmallcap',
    'DELCYCLES':  'NSmallcap','DHANI':      'NSmallcap',
    'DPWWORLD':   'NSmallcap','EUROBONDS':  'NSmallcap',
    'FLEX':       'NSmallcap','GMR':        'NSmallcap',
}

OUTPUT_DIR = 'Stock'


# ── helpers ──────────────────────────────────────────────────────────────────

def _flatten(df: pd.DataFrame) -> pd.DataFrame:
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df


def _download(symbol: str) -> pd.DataFrame:
    """Try primary .NS, then aliases. Returns clean OHLCV or empty."""
    candidates = [f"{symbol}.NS"] + ALIASES.get(symbol, [])
    seen, unique = set(), []
    for c in candidates:
        if c not in seen:
            seen.add(c); unique.append(c)

    for ticker in unique:
        if not ticker:
            continue
        try:
            raw = yf.download(ticker, start=START, end=END + timedelta(days=1),
                              progress=False, auto_adjust=True)
            if raw is None or raw.empty:
                continue
            raw = _flatten(raw.copy())
            lmap = {c.lower(): c for c in raw.columns}
            rename = {lmap[w.lower()]: w for w in OHLCV
                      if w not in raw.columns and w.lower() in lmap}
            if rename:
                raw.rename(columns=rename, inplace=True)
            if 'Close' not in raw.columns:
                continue
            if 'Volume' not in raw.columns:
                raw['Volume'] = 0
            raw.index = pd.to_datetime(raw.index).tz_localize(None)
            raw.index.name = 'Date'
            df = raw[[c for c in OHLCV if c in raw.columns]].sort_index()
            if not df.empty:
                logger.info(f"  ✓ {symbol} via {ticker}  ({len(df)} rows)")
                return df
        except Exception as e:
            logger.debug(f"  {ticker} failed: {e}")
        time.sleep(0.3)
    return pd.DataFrame()


def _save_individual(symbol: str, df: pd.DataFrame, index_code: str):
    """Save symbol-level CSV (mirrors what stock.py produces per symbol)."""
    path = os.path.join(OUTPUT_DIR, f"{index_code}_{symbol}.csv")
    df.to_csv(path)


def _merge_into_wide(index_code: str, symbol: str, df: pd.DataFrame):
    """
    Merge new symbol columns into the wide index CSV.
    Creates the wide CSV if it doesn't exist yet.
    """
    wide_path = os.path.join(OUTPUT_DIR, f"{index_code}.csv")

    renamed = df.copy()
    renamed.columns = [f"{symbol}_{c}" for c in renamed.columns]

    if os.path.exists(wide_path):
        existing = pd.read_csv(wide_path, index_col=0, parse_dates=True)
        existing.index = pd.to_datetime(existing.index).tz_localize(None)

        # Drop stale columns for this symbol if they exist
        drop_cols = [c for c in existing.columns if c.startswith(f"{symbol}_")]
        if drop_cols:
            existing.drop(columns=drop_cols, inplace=True)

        merged = pd.concat([existing, renamed], axis=1)
    else:
        merged = renamed

    merged = merged.loc[:, ~merged.columns.duplicated()]
    merged.to_csv(wide_path)
    logger.info(f"  Updated wide CSV: {wide_path}")


# ── Natural Rubber fix ────────────────────────────────────────────────────────

def fix_natural_rubber():
    """Re-collect Natural_Rubber using Indian tyre companies as proxy."""
    from datetime import datetime as dt
    COMM_DIR = 'Commodities'
    rubber_path = os.path.join(COMM_DIR, 'Natural_Rubber.csv')

    proxies = ['CEAT.NS', 'MRF.NS', 'APOLLOTYRE.NS']
    start_comm = datetime(2021, 1, 1)
    end_comm   = datetime.today()

    for ticker in proxies:
        try:
            raw = yf.download(ticker, start=start_comm,
                              end=end_comm + timedelta(days=1),
                              progress=False, auto_adjust=True)
            if raw is None or raw.empty:
                continue
            raw = _flatten(raw.copy())
            lmap = {c.lower(): c for c in raw.columns}
            rename = {lmap[w.lower()]: w for w in OHLCV
                      if w not in raw.columns and w.lower() in lmap}
            if rename:
                raw.rename(columns=rename, inplace=True)
            if 'Close' not in raw.columns:
                continue
            if 'Volume' not in raw.columns:
                raw['Volume'] = 0
            raw.index = pd.to_datetime(raw.index).tz_localize(None)
            raw.index.name = 'Date'
            df = raw[[c for c in OHLCV if c in raw.columns]].sort_index()
            if not df.empty:
                df.to_csv(rubber_path)
                logger.info(f"✓ Natural_Rubber saved via proxy {ticker}  ({len(df)} rows)")

                # Update master summary
                master_path = os.path.join(COMM_DIR, 'MASTER_SUMMARY.csv')
                if os.path.exists(master_path):
                    ms = pd.read_csv(master_path)
                    ms.loc[ms['commodity'] == 'Natural_Rubber', 'status'] = 'Success'
                    ms.loc[ms['commodity'] == 'Natural_Rubber', 'rows']   = len(df)
                    ms.to_csv(master_path, index=False)
                return
        except Exception as e:
            logger.debug(f"  {ticker}: {e}")
        time.sleep(0.5)

    logger.warning("✗ Natural_Rubber: no proxy data found")


# ── HYPE (Hyperliquid) via CCXT ───────────────────────────────────────────────

def fix_hype():
    """Fetch HYPE/USDT from Binance via CCXT (not on yfinance)."""
    try:
        import ccxt
    except ImportError:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--quiet', 'ccxt'])
        import ccxt

    CRYPTO_DIR = 'Crypto'
    path = os.path.join(CRYPTO_DIR, 'HYPE.csv')

    try:
        ex = ccxt.binance({'enableRateLimit': True})
        ex.load_markets()
        sym = 'HYPE/USDT'
        if sym not in ex.markets:
            logger.warning("HYPE/USDT not in Binance markets — truly unavailable")
            return

        since = int(datetime(2024, 1, 1).timestamp() * 1000)
        rows = []
        while True:
            batch = ex.fetch_ohlcv(sym, '1d', since=since, limit=1000)
            if not batch:
                break
            rows.extend(batch)
            if len(batch) < 1000:
                break
            since = batch[-1][0] + 86_400_000
            time.sleep(ex.rateLimit / 1000)

        if not rows:
            logger.warning("HYPE: no data from CCXT")
            return

        df = pd.DataFrame(rows, columns=['ts', 'Open', 'High', 'Low', 'Close', 'Volume'])
        df['Date'] = pd.to_datetime(df['ts'], unit='ms', utc=True).dt.tz_localize(None)
        df.set_index('Date', inplace=True)
        df = df[['Open', 'High', 'Low', 'Close', 'Volume']].sort_index()

        end_date = datetime.today()
        df = df[df.index <= end_date]
        df.to_csv(path)
        logger.info(f"✓ HYPE saved  ({len(df)} rows)")

        # metadata
        meta = {
            'name': 'Hyperliquid', 'symbol': 'HYPE', 'category': 'DeFi/Perps',
            'ccxt_symbol': sym, 'yf_symbol': 'N/A',
            'start_date': '2024-01-01', 'end_date': end_date.strftime('%Y-%m-%d'),
            'interval': '1 Day', 'total_rows': len(df),
            'actual_start': df.index.min().strftime('%Y-%m-%d'),
            'actual_end': df.index.max().strftime('%Y-%m-%d'),
        }
        pd.DataFrame([meta]).to_csv(
            os.path.join(CRYPTO_DIR, 'HYPE_metadata.csv'), index=False)

        # update master summary
        ms_path = os.path.join(CRYPTO_DIR, 'MASTER_SUMMARY.csv')
        if os.path.exists(ms_path):
            ms = pd.read_csv(ms_path)
            ms.loc[ms['symbol'] == 'HYPE', 'status'] = 'Success'
            ms.loc[ms['symbol'] == 'HYPE', 'rows']   = len(df)
            ms.to_csv(ms_path, index=False)

    except Exception as e:
        logger.warning(f"HYPE CCXT fix failed: {e}")


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    logger.info("=" * 60)
    logger.info("TARGETED RE-COLLECT FOR FAILED SYMBOLS")
    logger.info(f"Date range : {START.date()} → {END.date()}")
    logger.info("=" * 60)

    # ── 1. Stock symbols ─────────────────────────────────────────────────────
    to_fix = {sym: ALIASES.get(sym, []) for sym in ALIASES if ALIASES.get(sym) != []}
    # also include symbols with empty alias lists so they get a retry attempt
    to_fix_all = list(ALIASES.keys())

    succeeded, skipped, failed = [], [], []

    for symbol in tqdm(to_fix_all, desc="Fixing stock symbols"):
        index_code = SYMBOL_INDEX.get(symbol, 'N50')

        # Skip delisted with no alias
        if ALIASES.get(symbol) == []:
            logger.warning(f"  ⊘ {symbol}: delisted, no replacement — skipping")
            skipped.append(symbol)
            continue

        # Check if already collected successfully in existing wide CSV
        wide_path = os.path.join(OUTPUT_DIR, f"{index_code}.csv")
        if os.path.exists(wide_path):
            existing = pd.read_csv(wide_path, index_col=0, parse_dates=True, nrows=5)
            if any(c.startswith(f"{symbol}_") for c in existing.columns):
                logger.info(f"  ✓ {symbol}: already in {index_code}.csv — skipping")
                succeeded.append(symbol)
                continue

        df = _download(symbol)
        if not df.empty:
            _save_individual(symbol, df, index_code)
            _merge_into_wide(index_code, symbol, df)
            succeeded.append(symbol)
        else:
            logger.warning(f"  ✗ {symbol}: no data found")
            failed.append(symbol)

        time.sleep(0.2)

    # ── 2. Natural Rubber ────────────────────────────────────────────────────
    logger.info("\n" + "=" * 60)
    logger.info("Fixing Natural_Rubber (Commodity)")
    logger.info("=" * 60)
    fix_natural_rubber()

    # ── 3. HYPE (Hyperliquid) ────────────────────────────────────────────────
    logger.info("\n" + "=" * 60)
    logger.info("Fixing HYPE (Hyperliquid Crypto)")
    logger.info("=" * 60)
    fix_hype()

    # ── Summary ──────────────────────────────────────────────────────────────
    logger.info("\n" + "=" * 60)
    logger.info("RE-COLLECT COMPLETE")
    logger.info(f"  ✓ Succeeded : {len(succeeded)}  {succeeded}")
    logger.info(f"  ⊘ Skipped   : {len(skipped)}   {skipped}")
    logger.info(f"  ✗ Still fail: {len(failed)}   {failed}")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()
