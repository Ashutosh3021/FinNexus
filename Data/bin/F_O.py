"""
Data Collection Script for NSE Futures & Options
Combines multiple reliable sources for maximum coverage and redundancy
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import logging
from tqdm import tqdm
import warnings
import json
import subprocess
import sys
warnings.filterwarnings('ignore')

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Install required libraries if not present
def install_package(package):
    try:
        __import__(package)
    except ImportError:
        logger.info(f"Installing {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# Install required packages
required_packages = ['pandas', 'numpy', 'requests', 'beautifulsoup4']
for pkg in required_packages:
    install_package(pkg)

# Import libraries with fallback installation
try:
    from jugaad_data.nse import stock_df, index_df, NSELive, expiry_dates
except ImportError:
    logger.info("Installing jugaad-data...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "jugaad-data"])
    from jugaad_data.nse import stock_df, index_df, NSELive, expiry_dates

# Optional imports with graceful failure
ns = None
try:
    import nsefetch as ns
except ImportError:
    logger.warning("nsefetch not available, will skip this source")

nsefin = None
FnO = None
OptionChain = None
try:
    import nsefin
    from nsefin import FnO, OptionChain
except ImportError:
    logger.warning("nsefin not available, will skip this source")

nsepy = None
get_history = None
get_futures_data = None
get_option_data = None
try:
    import nsepy
    from nsepy import get_history
    from nsepy.derivatives import get_futures_data, get_option_data
except ImportError:
    logger.warning("nsepy not available, will skip this source")

class NSFuturesOptionsCollector:
    def __init__(self, start_date='2024-01-01', end_date='2026-06-22', output_dir='Futures_Options'):
        """
        Initialize the F&O data collector
        
        Args:
            start_date: Start date for data collection
            end_date: End date for data collection
            output_dir: Directory to save CSV files
        """
        self.start_date = datetime.strptime(start_date, '%Y-%m-%d')
        self.end_date = datetime.strptime(end_date, '%Y-%m-%d')
        self.output_dir = output_dir
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Define the assets to collect
        self.futures_assets = {
            'NIFTY_50_Futures': {
                'type': 'Index Futures',
                'symbol': 'NIFTY',
                'expiry': None  # Will get nearest expiry
            },
            'BANK_NIFTY_Futures': {
                'type': 'Index Futures',
                'symbol': 'BANKNIFTY',
                'expiry': None
            },
            'FINNIFTY_Futures': {
                'type': 'Index Futures',
                'symbol': 'FINNIFTY',
                'expiry': None
            },
            'HDFC_BANK_Futures': {
                'type': 'Stock Futures',
                'symbol': 'HDFCBANK',
                'expiry': None
            },
            'RELIANCE_Futures': {
                'type': 'Stock Futures',
                'symbol': 'RELIANCE',
                'expiry': None
            },
            'INFOSYS_Futures': {
                'type': 'Stock Futures',
                'symbol': 'INFY',
                'expiry': None
            }
        }
        
        self.options_assets = {
            'NIFTY_50_Options': {
                'type': 'Index Options',
                'symbol': 'NIFTY',
                'expiry': None
            },
            'BANK_NIFTY_Options': {
                'type': 'Index Options',
                'symbol': 'BANKNIFTY',
                'expiry': None
            },
            'FINNIFTY_Options': {
                'type': 'Index Options',
                'symbol': 'FINNIFTY',
                'expiry': None
            },
            'BRIGADE_Options': {
                'type': 'Stock Options',
                'symbol': 'BRIGADE',
                'expiry': None
            }
        }
        
        # Commodity options (different data source)
        self.commodity_assets = {
            'WTI_Oil_Options': {
                'type': 'Commodity Options',
                'symbol': 'WTI',
                'exchange': 'MCX'
            },
            'Brent_Oil_Options': {
                'type': 'Commodity Options',
                'symbol': 'BRENT',
                'exchange': 'MCX'
            }
        }
        
        # Initialize NSELive for real-time data
        self.nse_live = NSELive()
        logger.info("Initialized NSE F&O Data Collector")
    
    def get_expiry_dates(self, symbol):
        """
        Get available expiry dates for a symbol
        
        Args:
            symbol: Symbol name (e.g., 'NIFTY', 'BANKNIFTY')
            
        Returns:
            List of expiry dates
        """
        try:
            # Using jugaad-data's expiry_dates
            expiries = expiry_dates(symbol)
            if expiries:
                expiries = [e for e in expiries if e >= self.start_date and e <= self.end_date]
                return sorted(expiries)
            return []
        except Exception as e:
            logger.debug(f"Could not get expiry dates for {symbol}: {e}")
            return []
    
    def get_nearest_expiry(self, symbol):
        """
        Get the nearest expiry date for a symbol
        
        Args:
            symbol: Symbol name
            
        Returns:
            Nearest expiry date
        """
        expiries = self.get_expiry_dates(symbol)
        if expiries:
            return expiries[0]
        return None
    
    def fetch_futures_jugaad(self, symbol, expiry_date):
        """
        Fetch futures data using jugaad-data
        
        Args:
            symbol: Symbol name
            expiry_date: Expiry date
            
        Returns:
            DataFrame with futures data
        """
        # jugaad-data's derivatives_df doesn't support OHLC for specific expiries
        # Just return empty dataframe and rely on other sources
        return pd.DataFrame()
    
    def fetch_futures_nsefetch(self, symbol, expiry_date):
        """
        Fetch futures data using nsefetch
        
        Args:
            symbol: Symbol name
            expiry_date: Expiry date
            
        Returns:
            DataFrame with futures data
        """
        if ns is None:
            return pd.DataFrame()
        try:
            # Using nsefetch's get_futures_data
            data = ns.get_futures_data(symbol=symbol, expiry=expiry_date)
            if data is not None and not data.empty:
                # Standardize columns
                data = data[['OPEN', 'HIGH', 'LOW', 'CLOSE', 'VOLUME', 'OPEN_INT']].copy()
                data.columns = ['Open', 'High', 'Low', 'Close', 'Volume', 'Open Interest']
                data.index = pd.to_datetime(data.index)
                return data
            return pd.DataFrame()
        except Exception as e:
            logger.debug(f"nsefetch futures failed for {symbol}: {e}")
            return pd.DataFrame()

    def fetch_futures_nsefin(self, symbol, expiry_date):
        """
        Fetch futures data using nsefin
        
        Args:
            symbol: Symbol name
            expiry_date: Expiry date
            
        Returns:
            DataFrame with futures data
        """
        if nsefin is None or FnO is None:
            return pd.DataFrame()
        try:
            fno = FnO()
            data = fno.get_futures(symbol=symbol, expiry=expiry_date)
            if data is not None and not data.empty:
                # Standardize columns
                if 'OPEN' in data.columns:
                    data = data[['OPEN', 'HIGH', 'LOW', 'CLOSE', 'VOLUME', 'OPEN_INT']].copy()
                    data.columns = ['Open', 'High', 'Low', 'Close', 'Volume', 'Open Interest']
                    data.index = pd.to_datetime(data.index)
                    return data
            return pd.DataFrame()
        except Exception as e:
            logger.debug(f"nsefin futures failed for {symbol}: {e}")
            return pd.DataFrame()

    def fetch_futures_nsepy(self, symbol, expiry_date):
        """
        Fetch futures data using nsepy
        
        Args:
            symbol: Symbol name
            expiry_date: Expiry date
            
        Returns:
            DataFrame with futures data
        """
        if nsepy is None or get_futures_data is None:
            return pd.DataFrame()
        try:
            data = get_futures_data(
                symbol=symbol,
                expiry_date=expiry_date,
                start_date=self.start_date,
                end_date=self.end_date
            )
            if data is not None and not data.empty:
                # Standardize columns
                data = data[['OPEN', 'HIGH', 'LOW', 'CLOSE', 'VOLUME', 'OPEN_INT']].copy()
                data.columns = ['Open', 'High', 'Low', 'Close', 'Volume', 'Open Interest']
                data.index = pd.to_datetime(data.index)
                return data
            return pd.DataFrame()
        except Exception as e:
            logger.debug(f"nsepy futures failed for {symbol}: {e}")
            return pd.DataFrame()
    
    def fetch_futures_combined(self, symbol, expiry_date):
        """
        Fetch futures data using multiple sources
        
        Args:
            symbol: Symbol name
            expiry_date: Expiry date
            
        Returns:
            Combined DataFrame with futures data
        """
        dataframes = []
        sources_used = []
        
        # Try all sources
        sources = [
            ('jugaad', self.fetch_futures_jugaad),
            ('nsefetch', self.fetch_futures_nsefetch),
            ('nsefin', self.fetch_futures_nsefin),
            ('nsepy', self.fetch_futures_nsepy)
        ]
        
        for source_name, fetch_func in sources:
            try:
                df = fetch_func(symbol, expiry_date)
                if not df.empty:
                    dataframes.append(df)
                    sources_used.append(source_name)
                    logger.debug(f"✓ {source_name} returned {len(df)} rows for {symbol}")
            except Exception as e:
                logger.debug(f"✗ {source_name} failed for {symbol}: {e}")
        
        # Combine all data
        if dataframes:
            combined_df = dataframes[0].copy()
            for df in dataframes[1:]:
                combined_df = combined_df.combine_first(df)
            
            # Log which sources were used
            logger.info(f"Combined data for {symbol} from: {', '.join(sources_used)}")
            return combined_df
        else:
            logger.warning(f"No futures data found for {symbol}")
            return pd.DataFrame()
    
    def fetch_options_jugaad(self, symbol, expiry_date, option_type=None, strike_price=None):
        """
        Fetch options data using jugaad-data
        
        Args:
            symbol: Symbol name
            expiry_date: Expiry date
            option_type: 'CE' or 'PE' (optional)
            strike_price: Strike price (optional)
            
        Returns:
            DataFrame with options data
        """
        # jugaad-data's derivatives_df doesn't support OHLC for specific expiries
        # Just return empty dataframe and rely on other sources
        return pd.DataFrame()
    
    def fetch_options_nsefetch(self, symbol, expiry_date, option_type=None, strike_price=None):
        """
        Fetch options data using nsefetch
        
        Args:
            symbol: Symbol name
            expiry_date: Expiry date
            option_type: 'CE' or 'PE' (optional)
            strike_price: Strike price (optional)
            
        Returns:
            DataFrame with options data
        """
        if ns is None:
            return pd.DataFrame()
        try:
            data = ns.get_option_chain(symbol=symbol, expiry=expiry_date)
            if data is not None and not data.empty:
                # Filter by option type if specified
                if option_type:
                    data = data[data['OptionType'] == option_type]
                if strike_price:
                    data = data[data['StrikePrice'] == strike_price]
                
                # Standardize columns
                data = data[['OPEN', 'HIGH', 'LOW', 'CLOSE', 'VOLUME', 'OPEN_INT']].copy()
                data.columns = ['Open', 'High', 'Low', 'Close', 'Volume', 'Open Interest']
                data.index = pd.to_datetime(data.index)
                return data
            return pd.DataFrame()
        except Exception as e:
            logger.debug(f"nsefetch options failed for {symbol}: {e}")
            return pd.DataFrame()

    def fetch_options_nsefin(self, symbol, expiry_date, option_type=None, strike_price=None):
        """
        Fetch options data using nsefin
        
        Args:
            symbol: Symbol name
            expiry_date: Expiry date
            option_type: 'CE' or 'PE' (optional)
            strike_price: Strike price (optional)
            
        Returns:
            DataFrame with options data
        """
        if nsefin is None or OptionChain is None:
            return pd.DataFrame()
        try:
            option_chain = OptionChain(symbol=symbol)
            data = option_chain.get_options(expiry=expiry_date)
            if data is not None and not data.empty:
                # Filter by option type if specified
                if option_type:
                    data = data[data['Option Type'] == option_type]
                if strike_price:
                    data = data[data['Strike Price'] == strike_price]
                
                # Standardize columns
                data = data[['OPEN', 'HIGH', 'LOW', 'CLOSE', 'VOLUME', 'OPEN_INT']].copy()
                data.columns = ['Open', 'High', 'Low', 'Close', 'Volume', 'Open Interest']
                data.index = pd.to_datetime(data.index)
                return data
            return pd.DataFrame()
        except Exception as e:
            logger.debug(f"nsefin options failed for {symbol}: {e}")
            return pd.DataFrame()
    
    def fetch_options_combined(self, symbol, expiry_date, option_type=None, strike_price=None):
        """
        Fetch options data using multiple sources
        
        Args:
            symbol: Symbol name
            expiry_date: Expiry date
            option_type: 'CE' or 'PE' (optional)
            strike_price: Strike price (optional)
            
        Returns:
            Combined DataFrame with options data
        """
        dataframes = []
        sources_used = []
        
        # Try all sources
        sources = [
            ('jugaad', self.fetch_options_jugaad),
            ('nsefetch', self.fetch_options_nsefetch),
            ('nsefin', self.fetch_options_nsefin)
        ]
        
        for source_name, fetch_func in sources:
            try:
                df = fetch_func(symbol, expiry_date, option_type, strike_price)
                if not df.empty:
                    dataframes.append(df)
                    sources_used.append(source_name)
                    logger.debug(f"✓ {source_name} returned {len(df)} rows for {symbol}")
            except Exception as e:
                logger.debug(f"✗ {source_name} failed for {symbol}: {e}")
        
        # Combine all data
        if dataframes:
            combined_df = dataframes[0].copy()
            for df in dataframes[1:]:
                combined_df = combined_df.combine_first(df)
            
            logger.info(f"Combined options data for {symbol} from: {', '.join(sources_used)}")
            return combined_df
        else:
            logger.warning(f"No options data found for {symbol}")
            return pd.DataFrame()
    
    def collect_futures_data(self):
        """
        Collect futures data for all futures assets
        """
        logger.info("\n" + "=" * 60)
        logger.info("COLLECTING FUTURES DATA")
        logger.info("=" * 60)
        
        results = {}
        failed_assets = []
        
        for asset_name, asset_info in tqdm(self.futures_assets.items(), desc="Futures"):
            symbol = asset_info['symbol']
            logger.info(f"\nProcessing {asset_name} ({symbol})")
            
            # Get expiry date
            expiry_date = asset_info['expiry']
            if expiry_date is None:
                expiry_date = self.get_nearest_expiry(symbol)
                if expiry_date is None:
                    logger.error(f"Could not find expiry for {symbol}")
                    failed_assets.append(asset_name)
                    continue
                asset_info['expiry'] = expiry_date
            
            try:
                # Fetch data using combined approach
                df = self.fetch_futures_combined(symbol, expiry_date)
                
                if not df.empty:
                    # Save data
                    filename = os.path.join(self.output_dir, f"{asset_name}.csv")
                    df.to_csv(filename)
                    logger.info(f"✓ Saved {asset_name} to {filename} ({len(df)} rows)")
                    results[asset_name] = df
                else:
                    logger.error(f"✗ No data found for {asset_name}")
                    failed_assets.append(asset_name)
                
                # Small delay to avoid rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"✗ Error processing {asset_name}: {e}")
                failed_assets.append(asset_name)
        
        return results, failed_assets
    
    def collect_options_data(self):
        """
        Collect options data for all options assets
        """
        logger.info("\n" + "=" * 60)
        logger.info("COLLECTING OPTIONS DATA")
        logger.info("=" * 60)
        
        results = {}
        failed_assets = []
        
        for asset_name, asset_info in tqdm(self.options_assets.items(), desc="Options"):
            symbol = asset_info['symbol']
            logger.info(f"\nProcessing {asset_name} ({symbol})")
            
            # Get expiry date
            expiry_date = asset_info['expiry']
            if expiry_date is None:
                expiry_date = self.get_nearest_expiry(symbol)
                if expiry_date is None:
                    logger.error(f"Could not find expiry for {symbol}")
                    failed_assets.append(asset_name)
                    continue
                asset_info['expiry'] = expiry_date
            
            try:
                # For each option type (CE and PE)
                for option_type in ['CE', 'PE']:
                    logger.info(f"  Fetching {option_type} options...")
                    df = self.fetch_options_combined(symbol, expiry_date, option_type)
                    
                    if not df.empty:
                        # Save data with option type in filename
                        filename = os.path.join(self.output_dir, f"{asset_name}_{option_type}.csv")
                        df.to_csv(filename)
                        logger.info(f"    ✓ Saved {asset_name}_{option_type} ({len(df)} rows)")
                        results[f"{asset_name}_{option_type}"] = df
                    else:
                        logger.warning(f"    ✗ No {option_type} data found for {asset_name}")
                
                # Small delay to avoid rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"✗ Error processing {asset_name}: {e}")
                failed_assets.append(asset_name)
        
        return results, failed_assets
    
    def collect_commodity_options(self):
        """
        Collect commodity options data
        Note: This is a placeholder - commodity options data is typically available via MCX
        """
        logger.info("\n" + "=" * 60)
        logger.info("COLLECTING COMMODITY OPTIONS DATA")
        logger.info("=" * 60)
        logger.warning("Commodity options data (WTI, Brent) requires MCX-specific data sources")
        logger.warning("These are not available through NSE libraries")
        logger.warning("Consider using dedicated commodity data providers or MCX API")
        
        # Placeholder - return empty dict
        return {}, list(self.commodity_assets.keys())
    
    def save_master_summary(self, futures_results, options_results, futures_failed, options_failed):
        """
        Save a master summary of all collected data
        
        Args:
            futures_results: Dict of successful futures collections
            options_results: Dict of successful options collections
            futures_failed: List of failed futures assets
            options_failed: List of failed options assets
        """
        summary_data = []
        
        # Add futures
        for asset_name in self.futures_assets.keys():
            row = {
                'asset_name': asset_name,
                'type': 'Futures',
                'symbol': self.futures_assets[asset_name]['symbol'],
                'status': 'Success' if asset_name in futures_results else 'Failed',
                'rows': len(futures_results[asset_name]) if asset_name in futures_results else 0
            }
            summary_data.append(row)
        
        # Add options
        for asset_name in self.options_assets.keys():
            row = {
                'asset_name': asset_name,
                'type': 'Options',
                'symbol': self.options_assets[asset_name]['symbol'],
                'status': 'Success' if asset_name in options_results else 'Failed',
                'rows': len(options_results[asset_name]) if asset_name in options_results else 0
            }
            summary_data.append(row)
        
        # Add commodities
        for asset_name in self.commodity_assets.keys():
            row = {
                'asset_name': asset_name,
                'type': 'Commodity Options',
                'symbol': self.commodity_assets[asset_name]['symbol'],
                'status': 'Not Collected (MCX data required)',
                'rows': 0
            }
            summary_data.append(row)
        
        summary_df = pd.DataFrame(summary_data)
        filename = os.path.join(self.output_dir, 'MASTER_SUMMARY.csv')
        summary_df.to_csv(filename, index=False)
        logger.info(f"\n✓ Saved master summary to {filename}")
        
        # Print summary
        logger.info("\n" + "=" * 60)
        logger.info("COLLECTION SUMMARY")
        logger.info("=" * 60)
        success_count = sum(1 for row in summary_data if row['status'] == 'Success')
        total_count = len(summary_data)
        logger.info(f"Total assets: {total_count}")
        logger.info(f"Successfully collected: {success_count}")
        logger.info(f"Failed: {total_count - success_count}")
        logger.info(f"Output directory: {self.output_dir}")
        logger.info("=" * 60)
    
    def collect_all_data(self):
        """
        Collect all F&O data
        """
        logger.info("=" * 60)
        logger.info("NSE FUTURES & OPTIONS DATA COLLECTOR")
        logger.info("=" * 60)
        logger.info(f"Date range: {self.start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')}")
        logger.info(f"Output directory: {self.output_dir}")
        logger.info("=" * 60)
        
        # Collect futures
        futures_results, futures_failed = self.collect_futures_data()
        
        # Collect options
        options_results, options_failed = self.collect_options_data()
        
        # Collect commodity options (placeholder)
        commodity_results, commodity_failed = self.collect_commodity_options()
        
        # Save master summary
        self.save_master_summary(futures_results, options_results, futures_failed, options_failed)
        
        # Final output
        logger.info("\n" + "=" * 60)
        logger.info("✅ DATA COLLECTION COMPLETE!")
        logger.info(f"Futures: {len(futures_results)} collected, {len(futures_failed)} failed")
        logger.info(f"Options: {len(options_results)} collected, {len(options_failed)} failed")
        logger.info(f"Commodities: {len(commodity_results)} collected, {len(commodity_failed)} failed")
        logger.info("=" * 60)

def main():
    """
    Main function to run the data collection
    """
    # Configuration
    START_DATE = '2024-01-01'
    END_DATE = '2026-06-22'
    OUTPUT_DIR = 'Futures_Options'
    
    # Initialize collector
    collector = NSFuturesOptionsCollector(
        start_date=START_DATE,
        end_date=END_DATE,
        output_dir=OUTPUT_DIR
    )
    
    # Run collection
    collector.collect_all_data()

if __name__ == "__main__":
    main()