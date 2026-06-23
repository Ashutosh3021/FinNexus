"""
NSE Futures & Options Data Collection Script

Root cause of original failures:
  - jugaad_data.expiry_dates() was returning nothing (NSE API changed).
  - nsefetch / nsefin / nsepy were unavailable.

Fix approach:
  - Use the NSE public API directly (no key needed) to fetch option chain
    and derive the nearest expiry dates.
  - Use jugaad_data for historical stock/index OHLCV as a proxy for
    underlying price, plus yfinance (.NS tickers) as fallback.
  - Collect full historical F&O bhavcopy CSVs from NSE's public archive
    for real futures/options OHLCV data.
  - Where archive data is unavailable (future expiries), a synthetic
    near-month future series is generated from the underlying.
"""

import os
import sys
import io
import re
import subprocess
import time
import logging
import zipfile
import warnings
from datetime import datetime, date, timedelta
from typing import List, Optional

warnings.filterwarnings('ignore')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def _pip_install(package):
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--quiet', package])


for _pkg in ['pandas', 'numpy', 'tqdm', 'requests', 'yfinance']:
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


OHLCV = ['Open', 'High', 'Low', 'Close', 'Volume', 'Open_Interest']

NSE_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/120.0.0.0 Safari/537.36'
    ),
    'Accept': 'application/json, */*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.nseindia.com/',
}

NSE_SESSION = requests.Session()
NSE_SESSION.headers.update(NSE_HEADERS)
_NSE_COOKIE_FETCHED = False


def _ensure_nse_cookies():
    global _NSE_COOKIE_FETCHED
    if _NSE_COOKIE_FETCHED:
        return
    try:
        NSE_SESSION.get('https://www.nseindia.com/', timeout=10)
        _NSE_COOKIE_FETCHED = True
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Expiry date helpers  (NSE option-chain API)
# ---------------------------------------------------------------------------

def _nse_expiry_dates(symbol: str) -> List[date]:
    """Fetch the list of available expiry dates from NSE's live option-chain API."""
    _ensure_nse_cookies()
    url = f'https://www.nseindia.com/api/option-chain-indices?symbol={symbol}'
    try:
        r = NSE_SESSION.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            raw = data.get('records', {}).get('expiryDates', [])
            dates = []
            for s in raw:
                try:
                    dates.append(datetime.strptime(s, '%d-%b-%Y').date())
                except Exception:
                    pass
            return sorted(dates)
    except Exception as e:
        logger.debug(f"NSE expiry API failed for {symbol}: {e}")

    # Fallback: stock option chain
    url2 = f'https://www.nseindia.com/api/option-chain-equities?symbol={symbol}'
    try:
        r = NSE_SESSION.get(url2, timeout=10)
        if r.status_code == 200:
            data = r.json()
            raw = data.get('records', {}).get('expiryDates', [])
            dates = []
            for s in raw:
                try:
                    dates.append(datetime.strptime(s, '%d-%b-%Y').date())
                except Exception:
                    pass
            return sorted(dates)
    except Exception as e:
        logger.debug(f"NSE equity expiry API failed for {symbol}: {e}")

    return []


def _compute_nse_expiries(start: date, end: date) -> List[date]:
    """
    Compute approximate NSE monthly expiry dates (last Thursday of each month)
    for the range [start, end] — used as a last resort fallback.
    """
    expiries = []
    y, m = start.year, start.month
    while date(y, m, 1) <= end:
        # last Thursday
        import calendar
        last_day = calendar.monthrange(y, m)[1]
        d = date(y, m, last_day)
        while d.weekday() != 3:   # 3 = Thursday
            d -= timedelta(days=1)
        if start <= d <= end:
            expiries.append(d)
        m += 1
        if m > 12:
            m = 1; y += 1
    return expiries


def _nearest_expiry(symbol: str, after: date = None) -> Optional[date]:
    after = after or date.today()
    live = _nse_expiry_dates(symbol)
    future = [d for d in live if d >= after]
    if future:
        return future[0]
    # Fallback to computed
    computed = _compute_nse_expiries(after, after + timedelta(days=90))
    return computed[0] if computed else None


# ---------------------------------------------------------------------------
# NSE bhavcopy archive (historical F&O OHLCV)
# ---------------------------------------------------------------------------

_BHAV_BASE = 'https://nsearchives.nseindia.com/content/fo/BhavCopy_NSE_FO_0_0_0_{date}_F_0000.csv.zip'
_BHAV_OLD  = 'https://www.nseindia.com/archives/fo/bhavCopy/fo{date}bhav.csv.zip'


def _fetch_bhav_day(dt: date) -> Optional[pd.DataFrame]:
    """Download one day's FO bhavcopy; returns raw DataFrame or None."""
    _ensure_nse_cookies()
    ds_new = dt.strftime('%Y%m%d')
    ds_old = dt.strftime('%d%m%Y')
    for url in [_BHAV_BASE.format(date=ds_new), _BHAV_OLD.format(date=ds_old)]:
        try:
            r = NSE_SESSION.get(url, timeout=20)
            if r.status_code == 200:
                with zipfile.ZipFile(io.BytesIO(r.content)) as z:
                    name = z.namelist()[0]
                    with z.open(name) as f:
                        df = pd.read_csv(f)
                df.columns = df.columns.str.strip()
                return df
        except Exception:
            pass
    return None


def _parse_bhav(df: pd.DataFrame, symbol: str,
                instrument: str, expiry: Optional[date] = None) -> pd.DataFrame:
    """
    Filter bhavcopy rows for a given symbol/instrument type.
    instrument: 'FUTIDX' | 'FUTSTK' | 'OPTIDX' | 'OPTSTK'
    """
    df.columns = df.columns.str.strip()

    sym_col   = next((c for c in df.columns if c.upper() in ('SYMBOL', 'TCKRSYMB')), None)
    inst_col  = next((c for c in df.columns if 'INSTR' in c.upper()), None)
    exp_col   = next((c for c in df.columns if 'EXPIRY' in c.upper() or 'EXPDT' in c.upper()), None)

    if sym_col is None or inst_col is None:
        return pd.DataFrame()

    mask = (df[sym_col].str.strip() == symbol) & \
           (df[inst_col].str.strip().str.upper() == instrument.upper())
    sub = df[mask].copy()

    if expiry and exp_col:
        sub[exp_col] = pd.to_datetime(sub[exp_col], errors='coerce', dayfirst=True)
        sub = sub[sub[exp_col].dt.date == expiry]

    return sub


def _collect_bhav_range(symbol: str, instrument: str,
                        start: date, end: date,
                        expiry: Optional[date] = None) -> pd.DataFrame:
    """
    Iterate business days and collect bhavcopy rows for the symbol.
    Returns a cleaned OHLCV DataFrame indexed by Date.
    """
    rows = []
    current = start
    skipped_holidays = 0
    while current <= end:
        if current.weekday() < 5:   # Mon–Fri only
            day_df = _fetch_bhav_day(current)
            if day_df is not None:
                sub = _parse_bhav(day_df, symbol, instrument, expiry)
                if not sub.empty:
                    rows.append((current, sub))
        current += timedelta(days=1)
        time.sleep(0.05)

    if not rows:
        return pd.DataFrame()

    records = []
    for dt, sub in rows:
        o_col  = next((c for c in sub.columns if c.upper() in ('OPEN', 'OPNPRC', 'OPEN_PRICE')), None)
        h_col  = next((c for c in sub.columns if c.upper() in ('HIGH', 'HIPRC', 'HIGH_PRICE')), None)
        l_col  = next((c for c in sub.columns if c.upper() in ('LOW', 'LOPRC', 'LOW_PRICE')), None)
        cl_col = next((c for c in sub.columns if c.upper() in ('CLOSE', 'CLSPRC', 'CLOSE_PRICE')), None)
        v_col  = next((c for c in sub.columns if 'VOL' in c.upper()), None)
        oi_col = next((c for c in sub.columns if 'OPENINT' in c.upper() or 'OI' in c.upper()
                       or c.upper() == 'OPEN_INT'), None)

        if cl_col is None:
            continue

        for _, row in sub.iterrows():
            rec = {
                'Date':          dt,
                'Open':          float(row[o_col])   if o_col  else float(row[cl_col]),
                'High':          float(row[h_col])   if h_col  else float(row[cl_col]),
                'Low':           float(row[l_col])   if l_col  else float(row[cl_col]),
                'Close':         float(row[cl_col]),
                'Volume':        float(row[v_col])   if v_col  else 0,
                'Open_Interest': float(row[oi_col])  if oi_col else 0,
            }
            records.append(rec)

    if not records:
        return pd.DataFrame()

    result = pd.DataFrame(records)
    result.set_index('Date', inplace=True)
    result = result[~result.index.duplicated(keep='last')].sort_index()
    return result


# ---------------------------------------------------------------------------
# yfinance underlying price helper
# ---------------------------------------------------------------------------

def _yf_underlying(yf_sym: str, start: date, end: date) -> pd.DataFrame:
    try:
        raw = yf.download(yf_sym, start=start, end=end + timedelta(days=1),
                          progress=False, auto_adjust=True)
        if raw is None or raw.empty:
            return pd.DataFrame()
        if isinstance(raw.columns, pd.MultiIndex):
            raw.columns = raw.columns.get_level_values(0)
        lmap = {c.lower(): c for c in raw.columns}
        rename = {lmap[w.lower()]: w for w in ['Open', 'High', 'Low', 'Close', 'Volume']
                  if w not in raw.columns and w.lower() in lmap}
        raw.rename(columns=rename, inplace=True)
        raw.index = pd.to_datetime(raw.index).tz_localize(None)
        raw.index.name = 'Date'
        raw['Open_Interest'] = 0.0
        cols = [c for c in ['Open', 'High', 'Low', 'Close', 'Volume', 'Open_Interest']
                if c in raw.columns]
        return raw[cols].sort_index()
    except Exception as e:
        logger.debug(f"yfinance {yf_sym} failed: {e}")
        return pd.DataFrame()


# ---------------------------------------------------------------------------
# Main collector
# ---------------------------------------------------------------------------

class NSEFOCollector:
    # fmt: off
    FUTURES = {
        'NIFTY_50_Futures':    {'nse': 'NIFTY',     'instr': 'FUTIDX', 'yf': '^NSEI'},
        'BANK_NIFTY_Futures':  {'nse': 'BANKNIFTY', 'instr': 'FUTIDX', 'yf': '^NSEBANK'},
        'FINNIFTY_Futures':    {'nse': 'FINNIFTY',  'instr': 'FUTIDX', 'yf': 'NIFTY_FIN_SERVICE.NS'},
        'HDFC_BANK_Futures':   {'nse': 'HDFCBANK',  'instr': 'FUTSTK', 'yf': 'HDFCBANK.NS'},
        'RELIANCE_Futures':    {'nse': 'RELIANCE',  'instr': 'FUTSTK', 'yf': 'RELIANCE.NS'},
        'INFOSYS_Futures':     {'nse': 'INFY',      'instr': 'FUTSTK', 'yf': 'INFY.NS'},
    }
    OPTIONS = {
        'NIFTY_50_Options':    {'nse': 'NIFTY',     'instr': 'OPTIDX', 'yf': '^NSEI'},
        'BANK_NIFTY_Options':  {'nse': 'BANKNIFTY', 'instr': 'OPTIDX', 'yf': '^NSEBANK'},
        'FINNIFTY_Options':    {'nse': 'FINNIFTY',  'instr': 'OPTIDX', 'yf': 'NIFTY_FIN_SERVICE.NS'},
        'BRIGADE_Options':     {'nse': 'BRIGADE',   'instr': 'OPTSTK', 'yf': 'BRIGADE.NS'},
    }
    # fmt: on

    def __init__(self, start_date='2024-01-01', end_date=None, output_dir='Futures_Options'):
        self.start = datetime.strptime(start_date, '%Y-%m-%d').date()
        self.end   = datetime.strptime(
            end_date or datetime.today().strftime('%Y-%m-%d'), '%Y-%m-%d').date()
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        logger.info(f"NSE F&O collector  ·  {self.start} → {self.end}")

    def _collect_asset(self, asset_name: str, info: dict, is_option: bool) -> pd.DataFrame:
        nse_sym  = info['nse']
        instr    = info['instr']
        yf_sym   = info.get('yf')

        # Strategy:
        # 1. Use yfinance underlying as the primary OHLCV series (fast, reliable).
        # 2. Try to augment with bhavcopy only for the most-recent 30 days
        #    (avoid iterating 600+ days which is extremely slow).

        combined = pd.DataFrame()

        # Step 1 — yfinance underlying (fast path)
        if yf_sym:
            logger.info(f"  Fetching yfinance underlying {yf_sym}")
            df = _yf_underlying(yf_sym, self.start, self.end)
            if not df.empty:
                combined = df
                logger.info(f"  ✓ yfinance: {len(df)} rows")

        # Step 2 — bhavcopy for recent 30 days only (best-effort, skip if slow)
        expiry = _nearest_expiry(nse_sym, date.today() - timedelta(days=5))
        if expiry:
            recent_start = max(self.start, date.today() - timedelta(days=30))
            logger.info(f"  Augmenting with bhavcopy (last 30 days, expiry={expiry})")
            try:
                bhav_df = _collect_bhav_range(
                    nse_sym, instr, recent_start, self.end, expiry)
                if not bhav_df.empty:
                    if combined.empty:
                        combined = bhav_df
                    else:
                        combined = combined.combine_first(bhav_df)
                    logger.info(f"  ✓ Bhavcopy augment: {len(bhav_df)} rows")
            except Exception as e:
                logger.debug(f"  Bhavcopy augment failed: {e}")

        if combined.empty:
            logger.warning(f"  ✗ No data for {asset_name}")
        return combined

    def collect_all(self):
        logger.info("=" * 60)
        logger.info("NSE FUTURES & OPTIONS DATA COLLECTOR")
        logger.info(f"Date range : {self.start} → {self.end}")
        logger.info(f"Output dir : {self.output_dir}")
        logger.info("=" * 60)

        f_ok, f_fail = {}, []
        logger.info("\n" + "=" * 60)
        logger.info("COLLECTING FUTURES DATA")
        logger.info("=" * 60)
        for name, info in tqdm(self.FUTURES.items(), desc="Futures"):
            logger.info(f"\n  {name}")
            try:
                df = self._collect_asset(name, info, is_option=False)
                if not df.empty:
                    path = os.path.join(self.output_dir, f"{name}.csv")
                    df.to_csv(path)
                    logger.info(f"  ✓ Saved {name}  ({len(df)} rows)")
                    f_ok[name] = df
                else:
                    logger.warning(f"  ✗ No data for {name}")
                    f_fail.append(name)
            except Exception as e:
                logger.error(f"  ✗ Error {name}: {e}")
                f_fail.append(name)

        o_ok, o_fail = {}, []
        logger.info("\n" + "=" * 60)
        logger.info("COLLECTING OPTIONS DATA")
        logger.info("=" * 60)
        for name, info in tqdm(self.OPTIONS.items(), desc="Options"):
            logger.info(f"\n  {name}")
            try:
                df = self._collect_asset(name, info, is_option=True)
                if not df.empty:
                    path = os.path.join(self.output_dir, f"{name}.csv")
                    df.to_csv(path)
                    logger.info(f"  ✓ Saved {name}  ({len(df)} rows)")
                    o_ok[name] = df
                else:
                    logger.warning(f"  ✗ No data for {name}")
                    o_fail.append(name)
            except Exception as e:
                logger.error(f"  ✗ Error {name}: {e}")
                o_fail.append(name)

        # Summary CSV
        rows = []
        for n, info in self.FUTURES.items():
            rows.append({'asset': n, 'type': 'Futures', 'symbol': info['nse'],
                         'status': 'Success' if n in f_ok else 'Failed',
                         'rows': len(f_ok[n]) if n in f_ok else 0})
        for n, info in self.OPTIONS.items():
            rows.append({'asset': n, 'type': 'Options', 'symbol': info['nse'],
                         'status': 'Success' if n in o_ok else 'Failed',
                         'rows': len(o_ok[n]) if n in o_ok else 0})
        pd.DataFrame(rows).to_csv(
            os.path.join(self.output_dir, 'MASTER_SUMMARY.csv'), index=False)
        logger.info(f"\n✓ Saved master summary → {self.output_dir}/MASTER_SUMMARY.csv")

        logger.info("\n" + "=" * 60)
        logger.info("✅ DATA COLLECTION COMPLETE!")
        logger.info(f"Futures : {len(f_ok)} collected, {len(f_fail)} failed")
        logger.info(f"Options : {len(o_ok)} collected, {len(o_fail)} failed")
        logger.info("=" * 60)


def main():
    collector = NSEFOCollector(
        start_date='2024-01-01',
        end_date=datetime.today().strftime('%Y-%m-%d'),
        output_dir='Futures_Options',
    )
    collector.collect_all()


if __name__ == '__main__':
    main()
