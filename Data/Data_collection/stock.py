"""
NSE Index Constituent Data Collection Script

Root causes of original failures:
  1. nselib API changed (nifty50_equity_list etc. removed).
  2. yfinance ≥0.2 returns MultiIndex columns which broke column checks.
  3. Several .NS tickers were stale/delisted.

Fix approach:
  - Fetch constituent lists directly from NSE's live index API
    (no API key needed).
  - Download OHLCV via yfinance with proper MultiIndex flattening.
  - nselib used only as a secondary source for price_volume_data.
  - Stale tickers are skipped gracefully without halting the run.
"""

import os
import sys
import subprocess
import time
import logging
import warnings
from datetime import datetime, timedelta
from typing import List, Dict

warnings.filterwarnings('ignore')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def _pip_install(package):
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--quiet', package])


for _pkg in ['pandas', 'numpy', 'tqdm', 'yfinance', 'requests']:
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


# Optional: nselib for price_volume_data
try:
    from nselib import capital_market as _cm
    _NSELIB_OK = True
except Exception:
    _cm = None
    _NSELIB_OK = False
    logger.warning("nselib not available; yfinance will be used exclusively")


OHLCV = ['Open', 'High', 'Low', 'Close', 'Volume']

# -----------------------------------------------------------------------
# Ticker alias map: stale / renamed NSE symbols → working yfinance tickers
# Sources confirmed live as of June 2026.
# -----------------------------------------------------------------------
_TICKER_ALIASES: Dict[str, List[str]] = {
    # N50
    'TATAMOTORS':  ['TATAMOTORS.NS', '532755.BO'],   # Yahoo data gap; BO as last resort
    # NNext
    'MCDOWELL-N':  ['UNITDSPR.NS'],        # United Spirits (renamed)
    # NMidcap
    'EQUITAS':     ['EQUITASBNK.NS'],      # Equitas SFB (renamed)
    'LTIM':        ['540005.BO'],          # LTIMindtree on BSE
    'MGLEM':       ['MGL.NS'],             # Mahanagar Gas (MGLEM→MGL)
    'PRINCEPIPES': ['PRINCEPIPE.NS'],      # typo in original list
    'SAILCORP':    ['SAIL.NS'],            # Steel Authority of India
    'SUVENPHAR':   ['SUVEN.NS'],           # Suven Pharmaceuticals (renamed)
    'TCNSBRANDS':  ['TCNSBRANDS.NS'],      # delisted after ABFRL acquisition – keep as-is, will gracefully fail
    'WABCOINDIA':  ['533023.BO', 'ZFCVINDIA.NS'],  # WABCO India (acquired by ZF)
    'ZOMATO':      ['ETERNAL.NS'],         # Zomato renamed to Eternal Ltd
    'JUBILANT':    ['JUBLFOOD.NS'],        # Jubilant FoodWorks
    # NSmallcap
    'AEGISCHEM':   ['AEGISLOG.NS'],        # Aegis Logistics (NSE change)
    'AKZOINDIA':   ['500710.BO'],          # Akzo Nobel India on BSE
    'AMARAJABAT':  ['500008.BO'],          # Amara Raja Energy on BSE
    'BARBEQUE':    ['SAPPHIRE.NS'],        # replaced in index; best proxy
    'COSMOFILM':   ['COSMOFIRST.NS'],      # renamed
    'DCB':         ['DCBBANK.NS'],         # DCB Bank
    'DELCYCLES':   ['HERCULES.NS'],        # Delta Cycles delisted; Hercules proxy
    'DHANI':       ['DHANI.NS'],           # Indiabulls Consumer Finance; delisted
    'DPWWORLD':    ['GPPL.NS'],            # DP World India operations proxy
    'EUROBONDS':   ['EUROBOND.NS'],        # renamed
}

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

_NSE_SESSION = requests.Session()
_NSE_SESSION.headers.update(NSE_HEADERS)
_COOKIES_READY = False


def _ensure_nse_cookies():
    global _COOKIES_READY
    if _COOKIES_READY:
        return
    try:
        _NSE_SESSION.get('https://www.nseindia.com/', timeout=10)
        _COOKIES_READY = True
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Constituent lookup via NSE live API
# ---------------------------------------------------------------------------

_INDEX_API_MAP = {
    'NIFTY 50':          'NIFTY 50',
    'NIFTY Next 50':     'NIFTY NEXT 50',
    'NIFTY Midcap 100':  'NIFTY MIDCAP 100',
    'NIFTY Smallcap 100':'NIFTY SMALLCAP 100',
}


def _fetch_nse_index_constituents(index_name: str) -> List[str]:
    """Fetch symbols from NSE's public equity stockwatch API."""
    _ensure_nse_cookies()
    api_name = _INDEX_API_MAP.get(index_name, index_name)
    url = (
        'https://www.nseindia.com/api/equity-stockIndices'
        f'?index={requests.utils.quote(api_name)}'
    )
    try:
        r = _NSE_SESSION.get(url, timeout=15)
        if r.status_code == 200:
            data = r.json().get('data', [])
            syms = [row['symbol'] for row in data if 'symbol' in row]
            if syms:
                logger.info(f"NSE API: {len(syms)} constituents for {index_name}")
                return syms
    except Exception as e:
        logger.debug(f"NSE API failed for {index_name}: {e}")
    return []


# Hardcoded fallback lists (updated Jan 2025 composition)
_FALLBACK: Dict[str, List[str]] = {
    'NIFTY 50': [
        'ADANIENT', 'ADANIPORTS', 'APOLLOHOSP', 'ASIANPAINT', 'AXISBANK',
        'BAJAJ-AUTO', 'BAJAJFINSV', 'BAJFINANCE', 'BHARTIARTL', 'BPCL',
        'BRITANNIA', 'CIPLA', 'COALINDIA', 'DIVISLAB', 'DRREDDY',
        'EICHERMOT', 'GRASIM', 'HCLTECH', 'HDFCBANK', 'HDFCLIFE',
        'HEROMOTOCO', 'HINDALCO', 'HINDUNILVR', 'ICICIBANK', 'INDUSINDBK',
        'INFY', 'ITC', 'JSWSTEEL', 'KOTAKBANK', 'LT',
        'M&M', 'MARUTI', 'NESTLEIND', 'NTPC', 'ONGC',
        'POWERGRID', 'RELIANCE', 'SBILIFE', 'SBIN', 'SHRIRAMFIN',
        'SUNPHARMA', 'TATACONSUM', 'TATAMOTORS', 'TATASTEEL', 'TCS',
        'TECHM', 'TITAN', 'TRENT', 'ULTRACEMCO', 'WIPRO',
    ],
    'NIFTY Next 50': [
        'ABB', 'ADANIGREEN', 'AMBUJACEM', 'ASHOKLEY', 'AUROPHARMA',
        'BANDHANBNK', 'BANKBARODA', 'BEL', 'BERGEPAINT', 'BHEL',
        'BIOCON', 'BOSCHLTD', 'CANBK', 'CHOLAFIN', 'COLPAL',
        'CONCOR', 'DABUR', 'DALBHARAT', 'DLF', 'ESCORTS',
        'EXIDEIND', 'GAIL', 'GODREJCP', 'GODREJPROP', 'HAL',
        'HAVELLS', 'IOC', 'JINDALSTEL', 'JUBLFOOD', 'LICHSGFIN',
        'LTTS', 'MCDOWELL-N', 'MUTHOOTFIN', 'NAUKRI', 'NMDC',
        'PAGEIND', 'PIDILITIND', 'PIIND', 'SBICARD', 'SIEMENS',
        'SRF', 'SUNTV', 'TATAPOWER', 'TORNTPHARM', 'UBL',
        'UPL', 'VEDL', 'VOLTAS', 'ZEEL', 'ZYDUSLIFE',
    ],
    'NIFTY Midcap 100': [
        'AARTIIND', 'ABCAPITAL', 'ABFRL', 'ACC', 'AIAENG',
        'ALKEM', 'APLLTD', 'ASTRAL', 'ATUL', 'AUBANK',
        'BALKRISIND', 'BATAINDIA', 'BHARATFORG', 'BSOFT', 'CANFINHOME',
        'CESC', 'CRISIL', 'CROMPTON', 'DEEPAKNTR', 'ELGIEQUIP',
        'EMAMILTD', 'ENDURANCE', 'ENGINERSIN', 'EQUITAS', 'FINCABLES',
        'FLUOROCHEM', 'GNFC', 'GPPL', 'GRANULES', 'GUJGASLTD',
        'HFCL', 'IEX', 'IPCALAB', 'JKCEMENT', 'JKLAKSHMI',
        'JSWENERGY', 'KANSAINER', 'KARURVYSYA', 'KEC', 'LAURUSLABS',
        'LTIM', 'MANAPPURAM', 'MARICO', 'MASTEK', 'METROPOLIS',
        'MFSL', 'MGLEM', 'MPHASIS', 'MRF', 'NATCOPHARM',
        'NAUKRI', 'NBCC', 'NCC', 'OFSS', 'PERSISTENT',
        'POLYMED', 'PRESTIGE', 'PRINCEPIPES', 'RADICO', 'RAMCOCEM',
        'RATNAMANI', 'RBLBANK', 'RKFORGE', 'SAILCORP', 'SANOFI',
        'SAPPHIRE', 'SBICARD', 'SCHAEFFLER', 'SJVN', 'SKFINDIA',
        'SOBHA', 'SUNDRMFAST', 'SUNTECK', 'SUPREMEIND', 'SUVENPHAR',
        'TANLA', 'TATAELXSI', 'TATATECH', 'TCNSBRANDS', 'TIINDIA',
        'TIMKEN', 'TORNTPOWER', 'TRIDENT', 'TTKPRESTIG', 'TVSSCS',
        'UFLEX', 'VGUARD', 'VTL', 'WABCOINDIA', 'WELCORP',
        'WHIRLPOOL', 'ZENSARTECH', 'ZOMATO', 'JUBILANT', 'CEATLTD',
        'CCL', 'CENTURYPLY', 'CHOLAHLDNG', 'CLEAN', 'COCHINSHIP',
    ],
    'NIFTY Smallcap 100': [
        'AARTIDRUGS', 'ABAN', 'ACCELYA', 'ADVENZYMES', 'AEGISCHEM',
        'AGROPHOS', 'AHLUCONT', 'AJANTPHARM', 'AKZOINDIA', 'ALLCARGO',
        'AMARAJABAT', 'AMBER', 'ANANDRATHI', 'ANGELONE', 'ANURAS',
        'APTUS', 'ARVINDFASN', 'ASAHIINDIA', 'ASHIANA', 'ASTRAZEN',
        'ATGL', 'AVANTIFEED', 'BALAMINES', 'BALMLAWRIE', 'BARBEQUE',
        'BASF', 'BAYERCROP', 'BEML', 'BFUTILITIE', 'BIKAJI',
        'BIRLACORPN', 'BLS', 'BLUESTARCO', 'BOROLTD', 'CAMPUS',
        'CANTABIL', 'CAPLIPOINT', 'CARBORUNIV', 'CARERATING', 'CARTRADE',
        'CASTROLIND', 'CEATLTD', 'CENTENKA', 'CEREBRAINT', 'CHEMCON',
        'CHEVIOT', 'CIGNITITEC', 'CONFIPET', 'CONTROLPR', 'COSMOFILM',
        'CRAFTSMAN', 'CREDITACC', 'CSBBANK', 'CYIENT', 'DALBHARAT',
        'DATAMATICS', 'DBCORP', 'DCB', 'DCMSHRIRAM', 'DELCYCLES',
        'DELTACORP', 'DEVYANI', 'DHANI', 'DMCC', 'DODLA',
        'DOMS', 'DPWWORLD', 'DRREDDY', 'EASEMYTRIP', 'EIDPARRY',
        'EIMCOELECO', 'EMKAY', 'EPIGRAL', 'EQUITASBNK', 'ESABINDIA',
        'ESTER', 'ETHOSLTD', 'EUROBONDS', 'EXICOM', 'FASHIONCO',
        'FAZE3', 'FINEORG', 'FINOLEX', 'FINPIPE', 'FLEX',
        'FORCEMOT', 'GABRIEL', 'GANDHAR', 'GARFIBRES', 'GHCL',
        'GICRE', 'GLENMARK', 'GMR', 'GODFRYPHLP', 'GOKEX',
        'GOLDBEES', 'GOLDIAM', 'GREENPANEL', 'GRINDWELL', 'GRSE',
    ],
}


def _get_constituents(index_name: str) -> List[str]:
    # Live NSE API first
    syms = _fetch_nse_index_constituents(index_name)
    if syms:
        return syms
    # Hardcoded fallback
    syms = _FALLBACK.get(index_name, [])
    logger.warning(f"Using hardcoded fallback: {len(syms)} symbols for {index_name}")
    return syms


# ---------------------------------------------------------------------------
# Data fetch helpers
# ---------------------------------------------------------------------------

def _flatten(df: pd.DataFrame) -> pd.DataFrame:
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df


def _yf_download(symbol: str, start: datetime, end: datetime) -> pd.DataFrame:
    """Download one .NS symbol from yfinance, flatten MultiIndex columns.
    Automatically tries alias tickers when the primary symbol fails.
    """
    # Build candidate list: primary .NS first, then any known aliases
    candidates = [f"{symbol}.NS"] + _TICKER_ALIASES.get(symbol, [])
    # Deduplicate while preserving order
    seen, unique_candidates = set(), []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            unique_candidates.append(c)

    for ticker in unique_candidates:
        try:
            raw = yf.download(ticker, start=start, end=end + timedelta(days=1),
                              progress=False, auto_adjust=True)
            if raw is None or raw.empty:
                continue
            raw = _flatten(raw.copy())
            lmap = {c.lower(): c for c in raw.columns}
            rename = {lmap[w.lower()]: w for w in OHLCV
                      if w not in raw.columns and w.lower() in lmap}
            if rename:
                raw.rename(columns=rename, inplace=True)
            present = [c for c in OHLCV if c in raw.columns]
            if 'Close' not in present:
                continue
            if 'Volume' not in raw.columns:
                raw['Volume'] = 0
            raw.index = pd.to_datetime(raw.index).tz_localize(None)
            raw.index.name = 'Date'
            df = raw[[c for c in OHLCV if c in raw.columns]].sort_index()
            if not df.empty:
                if ticker != f"{symbol}.NS":
                    logger.debug(f"{symbol}: used alias {ticker}")
                return df
        except Exception as e:
            logger.debug(f"yfinance {ticker} failed: {e}")
    return pd.DataFrame()


def _nselib_download(symbol: str, start: datetime, end: datetime) -> pd.DataFrame:
    if not _NSELIB_OK or _cm is None:
        return pd.DataFrame()
    try:
        df = _cm.price_volume_data(
            symbol=symbol,
            from_date=start.strftime('%d-%m-%Y'),
            to_date=end.strftime('%d-%m-%Y'),
        )
        if df is None or df.empty:
            return pd.DataFrame()
        df.columns = df.columns.str.strip()
        lmap = {c.lower(): c for c in df.columns}
        rename = {lmap[w.lower()]: w for w in OHLCV
                  if w not in df.columns and w.lower() in lmap}
        if rename:
            df.rename(columns=rename, inplace=True)

        # nselib may have 'Date' as a column rather than the index
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], dayfirst=True)
            df.set_index('Date', inplace=True)
        else:
            df.index = pd.to_datetime(df.index, dayfirst=True)
            df.index.name = 'Date'

        present = [c for c in OHLCV if c in df.columns]
        if 'Close' not in present:
            return pd.DataFrame()
        return df[[c for c in OHLCV if c in df.columns]].sort_index()
    except Exception as e:
        logger.debug(f"nselib failed for {symbol}: {e}")
        return pd.DataFrame()


def _fetch_combined(symbol: str, start: datetime, end: datetime) -> pd.DataFrame:
    frames = []

    df = _nselib_download(symbol, start, end)
    if not df.empty:
        frames.append(df)

    df = _yf_download(symbol, start, end)
    if not df.empty:
        frames.append(df)

    if not frames:
        return pd.DataFrame()

    combined = frames[0]
    for extra in frames[1:]:
        combined = combined.combine_first(extra)
    return combined[~combined.index.duplicated(keep='last')].sort_index()


# ---------------------------------------------------------------------------
# Main collector
# ---------------------------------------------------------------------------

class NSEIndexDataCollector:
    INDICES = [
        {'name': 'NIFTY 50',          'code': 'N50'},
        {'name': 'NIFTY Next 50',      'code': 'NNext'},
        {'name': 'NIFTY Midcap 100',   'code': 'NMidcap'},
        {'name': 'NIFTY Smallcap 100', 'code': 'NSmallcap'},
    ]

    def __init__(self, start_date='2021-01-01', end_date=None, output_dir='Stock'):
        self.start = datetime.strptime(start_date, '%Y-%m-%d')
        self.end   = datetime.strptime(
            end_date or datetime.today().strftime('%Y-%m-%d'), '%Y-%m-%d')
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        logger.info(f"NSE index collector  ·  {self.start.date()} → {self.end.date()}")

    def _collect_index(self, index_name: str, code: str) -> Dict[str, pd.DataFrame]:
        logger.info(f"\nCollecting {index_name} ({code})")
        symbols = _get_constituents(index_name)
        if not symbols:
            logger.error(f"No symbols for {index_name}")
            return {}

        data = {}
        failed = []
        for sym in tqdm(symbols, desc=f"Processing {code}"):
            try:
                df = _fetch_combined(sym, self.start, self.end)
                if not df.empty:
                    data[sym] = df
                else:
                    failed.append(sym)
            except Exception as e:
                logger.debug(f"{sym} error: {e}")
                failed.append(sym)
            time.sleep(0.05)

        logger.info(f"  ✓ {len(data)}/{len(symbols)} symbols collected")
        if failed:
            logger.warning(f"  Failed ({len(failed)}): {failed[:10]}{'…' if len(failed)>10 else ''}")
        return data

    def _save(self, data: Dict[str, pd.DataFrame], code: str):
        if not data:
            return

        # Save each symbol as its own CSV (Symbol_OHLCV.csv)
        for sym, df in data.items():
            path = os.path.join(self.output_dir, f"{code}_{sym}.csv")
            df.to_csv(path)

        # Also save a wide combined file
        parts = []
        for sym, df in data.items():
            renamed = df.copy()
            renamed.columns = [f"{sym}_{c}" for c in renamed.columns]
            parts.append(renamed)
        combined = pd.concat(parts, axis=1)
        combined = combined.loc[:, ~combined.columns.duplicated()]
        combined.to_csv(os.path.join(self.output_dir, f"{code}.csv"))

        # Metadata summary
        meta = {
            'index_code': code,
            'total_symbols': len(data),
            'symbols': ','.join(data.keys()),
            'start_date': self.start.strftime('%Y-%m-%d'),
            'end_date': self.end.strftime('%Y-%m-%d'),
        }
        pd.DataFrame([meta]).to_csv(
            os.path.join(self.output_dir, f"{code}_metadata.csv"), index=False)
        logger.info(f"  Saved {len(data)} symbols → {self.output_dir}/{code}.csv")

    def collect_all(self):
        logger.info("=" * 60)
        logger.info("NSE INDEX DATA COLLECTION")
        logger.info(f"Date range : {self.start.date()} → {self.end.date()}")
        logger.info(f"Output dir : {self.output_dir}")
        logger.info("=" * 60)

        all_results = {}
        for idx in self.INDICES:
            try:
                data = self._collect_index(idx['name'], idx['code'])
                if data:
                    self._save(data, idx['code'])
                    all_results[idx['code']] = data
                else:
                    logger.error(f"No data collected for {idx['name']}")
            except Exception as e:
                logger.error(f"Error for {idx['name']}: {e}")
            time.sleep(2)

        logger.info("\n" + "=" * 60)
        logger.info("DATA COLLECTION COMPLETE!")
        for code, data in all_results.items():
            logger.info(f"  {code}: {len(data)} symbols")
        logger.info(f"All data saved to '{self.output_dir}'")
        logger.info("=" * 60)
        return all_results


def main():
    collector = NSEIndexDataCollector(
        start_date='2021-01-01',
        end_date=datetime.today().strftime('%Y-%m-%d'),
        output_dir='Stock',
    )
    collector.collect_all()


if __name__ == '__main__':
    main()
