"""
Cryptocurrency Data Collection Script
Combines CoinGecko (ml4t-data), CCXT, and yfinance for maximum coverage
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import logging
from tqdm import tqdm
import warnings
import sys
import subprocess
import json
warnings.filterwarnings('ignore')

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Install required libraries
def install_package(package):
    try:
        __import__(package)
    except ImportError:
        logger.info(f"Installing {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# Install all required packages
required_packages = ['pandas', 'numpy', 'requests', 'python-dotenv', 'tqdm', 'ccxt', 'yfinance']
for pkg in required_packages:
    install_package(pkg)

# Import libraries with fallback installation
try:
    from ml4t.data.providers import CoinGeckoProvider
except ImportError:
    logger.info("Installing ml4t-data...")
    os.system('pip install ml4t-data')
    from ml4t.data.providers import CoinGeckoProvider

try:
    import ccxt
except ImportError:
    logger.info("Installing ccxt...")
    os.system('pip install ccxt')
    import ccxt

try:
    import yfinance as yf
except ImportError:
    logger.info("Installing yfinance...")
    os.system('pip install yfinance')
    import yfinance as yf

class CryptoDataCollector:
    def __init__(self, start_date='2024-01-01', end_date='2026-06-22', output_dir='Crypto'):
        """
        Initialize the cryptocurrency data collector
        
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
        
        # Define cryptocurrencies with their identifiers
        self.cryptos = {
            'Bitcoin': {
                'symbol': 'BTC',
                'coingecko_id': 'bitcoin',
                'ccxt_symbol': 'BTC/USDT',
                'yfinance_symbol': 'BTC-USD',
                'category': 'Store of Value'
            },
            'Ethereum': {
                'symbol': 'ETH',
                'coingecko_id': 'ethereum',
                'ccxt_symbol': 'ETH/USDT',
                'yfinance_symbol': 'ETH-USD',
                'category': 'Smart Contract'
            },
            'Solana': {
                'symbol': 'SOL',
                'coingecko_id': 'solana',
                'ccxt_symbol': 'SOL/USDT',
                'yfinance_symbol': 'SOL-USD',
                'category': 'Smart Contract'
            },
            'BNB': {
                'symbol': 'BNB',
                'coingecko_id': 'binancecoin',
                'ccxt_symbol': 'BNB/USDT',
                'yfinance_symbol': 'BNB-USD',
                'category': 'Exchange/Utility'
            },
            'TRON': {
                'symbol': 'TRX',
                'coingecko_id': 'tron',
                'ccxt_symbol': 'TRX/USDT',
                'yfinance_symbol': 'TRX-USD',
                'category': 'Payments/Stable'
            },
            'Monero': {
                'symbol': 'XMR',
                'coingecko_id': 'monero',
                'ccxt_symbol': 'XMR/USDT',
                'yfinance_symbol': 'XMR-USD',
                'category': 'Privacy'
            },
            'Litecoin': {
                'symbol': 'LTC',
                'coingecko_id': 'litecoin',
                'ccxt_symbol': 'LTC/USDT',
                'yfinance_symbol': 'LTC-USD',
                'category': 'Payments'
            },
            'Hyperliquid': {
                'symbol': 'HYPE',
                'coingecko_id': 'hyperliquid',
                'ccxt_symbol': 'HYPE/USDT',
                'yfinance_symbol': None,  # Not available on yfinance
                'category': 'DeFi/Perps'
            },
            'Uniswap': {
                'symbol': 'UNI',
                'coingecko_id': 'uniswap',
                'ccxt_symbol': 'UNI/USDT',
                'yfinance_symbol': 'UNI-USD',
                'category': 'DeFi/Exchange'
            },
            'Worldcoin': {
                'symbol': 'WLD',
                'coingecko_id': 'worldcoin',
                'ccxt_symbol': 'WLD/USDT',
                'yfinance_symbol': None,  # Not available on yfinance
                'category': 'AI'
            }
        }
        
        # Initialize providers
        self.coingecko_provider = None
        self.ccxt_exchange = None
        self.cache_dir = os.path.join(output_dir, '.cache')
        os.makedirs(self.cache_dir, exist_ok=True)
        
        self.initialize_providers()
        
        logger.info("Initialized Cryptocurrency Data Collector")
        logger.info(f"Total cryptocurrencies: {len(self.cryptos)}")
    
    def initialize_providers(self):
        """Initialize data providers"""
        try:
            # Initialize CoinGecko via ml4t-data
            self.coingecko_provider = CoinGeckoProvider()
            logger.info("✓ CoinGecko provider initialized")
        except Exception as e:
            logger.warning(f"CoinGecko initialization failed: {e}")
        
        try:
            # Initialize CCXT with Binance
            self.ccxt_exchange = ccxt.binance({
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'spot'
                }
            })
            self.ccxt_exchange.load_markets()
            logger.info("✓ CCXT (Binance) provider initialized")
        except Exception as e:
            logger.warning(f"CCXT initialization failed: {e}")
        
        logger.info("✓ yfinance available for fallback")
    
    def fetch_from_coingecko(self, crypto_info, start_date, end_date):
        """
        Fetch cryptocurrency data from CoinGecko via ml4t-data
        
        Args:
            crypto_info: Dictionary with crypto information
            start_date: Start date
            end_date: End date
            
        Returns:
            DataFrame with OHLCV data
        """
        if not self.coingecko_provider:
            return pd.DataFrame()
        
        try:
            # CoinGecko ID for the cryptocurrency
            coin_id = crypto_info['coingecko_id']
            
            # Get historical data
            df = self.coingecko_provider.fetch_ohlcv(
                symbol=coin_id,
                start=start_date.strftime('%Y-%m-%d'),
                end=end_date.strftime('%Y-%m-%d'),
                frequency='daily'
            )
            
            if df is not None and not df.is_empty():
                # Convert polars DataFrame to pandas
                df_pd = df.to_pandas()
                
                # Standardize columns
                df_pd.columns = ['timestamp', 'symbol', 'Open', 'High', 'Low', 'Close', 'Volume']
                df_pd['Date'] = pd.to_datetime(df_pd['timestamp'], unit='ms')
                df_pd.set_index('Date', inplace=True)
                df_pd = df_pd[['Open', 'High', 'Low', 'Close', 'Volume']]
                
                # Filter by date range
                mask = (df_pd.index >= start_date) & (df_pd.index <= end_date)
                df_pd = df_pd.loc[mask]
                
                logger.debug(f"CoinGecko: Retrieved {len(df_pd)} rows for {crypto_info['symbol']}")
                return df_pd
            
            return pd.DataFrame()
        except Exception as e:
            logger.debug(f"CoinGecko failed for {crypto_info['symbol']}: {e}")
            return pd.DataFrame()
    
    def fetch_from_ccxt(self, crypto_info, start_date, end_date):
        """
        Fetch cryptocurrency data from CCXT (Binance)
        
        Args:
            crypto_info: Dictionary with crypto information
            start_date: Start date
            end_date: End date
            
        Returns:
            DataFrame with OHLCV data
        """
        if not self.ccxt_exchange:
            return pd.DataFrame()
        
        try:
            symbol = crypto_info['ccxt_symbol']
            
            # Convert dates to milliseconds
            since = int(start_date.timestamp() * 1000)
            
            # Fetch OHLCV data
            ohlcv = self.ccxt_exchange.fetch_ohlcv(
                symbol=symbol,
                timeframe='1d',
                since=since,
                limit=1000  # Max per request
            )
            
            if ohlcv:
                # Convert to DataFrame
                df = pd.DataFrame(ohlcv, columns=['timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
                df['Date'] = pd.to_datetime(df['timestamp'], unit='ms')
                df.set_index('Date', inplace=True)
                df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
                
                # Filter by date range
                mask = (df.index >= start_date) & (df.index <= end_date)
                df = df.loc[mask]
                
                # If we need more data, fetch in chunks
                if len(df) < (end_date - start_date).days:
                    logger.debug(f"CCXT: Retrieved {len(df)} rows for {crypto_info['symbol']} (partial)")
                    # Try to get more data with another request
                    if len(ohlcv) == 1000:
                        # Get the last timestamp and fetch more
                        last_timestamp = ohlcv[-1][0]
                        additional = self.ccxt_exchange.fetch_ohlcv(
                            symbol=symbol,
                            timeframe='1d',
                            since=last_timestamp + 86400000,  # Next day
                            limit=1000
                        )
                        if additional:
                            df2 = pd.DataFrame(additional, columns=['timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
                            df2['Date'] = pd.to_datetime(df2['timestamp'], unit='ms')
                            df2.set_index('Date', inplace=True)
                            df2 = df2[['Open', 'High', 'Low', 'Close', 'Volume']]
                            mask = (df2.index >= start_date) & (df2.index <= end_date)
                            df2 = df2.loc[mask]
                            df = pd.concat([df, df2]).drop_duplicates()
                
                logger.debug(f"CCXT: Retrieved {len(df)} rows for {crypto_info['symbol']}")
                return df
            
            return pd.DataFrame()
        except Exception as e:
            logger.debug(f"CCXT failed for {crypto_info['symbol']}: {e}")
            return pd.DataFrame()
    
    def fetch_from_yfinance(self, crypto_info, start_date, end_date):
        """
        Fetch cryptocurrency data from yfinance (fallback)
        
        Args:
            crypto_info: Dictionary with crypto information
            start_date: Start date
            end_date: End date
            
        Returns:
            DataFrame with OHLCV data
        """
        yf_symbol = crypto_info.get('yfinance_symbol')
        if not yf_symbol:
            return pd.DataFrame()
        
        try:
            # Download data
            df = yf.download(yf_symbol, start=start_date, end=end_date, progress=False)
            
            if not df.empty:
                # Standardize columns
                df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
                df.index.name = 'Date'
                logger.debug(f"yfinance: Retrieved {len(df)} rows for {crypto_info['symbol']}")
                return df
            
            return pd.DataFrame()
        except Exception as e:
            logger.debug(f"yfinance failed for {crypto_info['symbol']}: {e}")
            return pd.DataFrame()
    
    def fetch_combined(self, crypto_name, crypto_info, start_date, end_date):
        """
        Fetch cryptocurrency data from multiple sources and combine
        
        Args:
            crypto_name: Name of the cryptocurrency
            crypto_info: Dictionary with crypto information
            start_date: Start date
            end_date: End date
            
        Returns:
            Combined DataFrame with data from all sources
        """
        dataframes = []
        sources_used = []
        
        # Try CoinGecko first (primary)
        df1 = self.fetch_from_coingecko(crypto_info, start_date, end_date)
        if not df1.empty:
            dataframes.append(df1)
            sources_used.append('CoinGecko')
            logger.debug(f"✓ CoinGecko: {len(df1)} rows for {crypto_name}")
        
        # Try CCXT second (primary)
        df2 = self.fetch_from_ccxt(crypto_info, start_date, end_date)
        if not df2.empty:
            dataframes.append(df2)
            sources_used.append('CCXT')
            logger.debug(f"✓ CCXT: {len(df2)} rows for {crypto_name}")
        
        # Try yfinance as fallback
        df3 = self.fetch_from_yfinance(crypto_info, start_date, end_date)
        if not df3.empty:
            dataframes.append(df3)
            sources_used.append('yfinance')
            logger.debug(f"✓ yfinance: {len(df3)} rows for {crypto_name}")
        
        # Combine all data
        if dataframes:
            # Start with the first dataframe
            combined_df = dataframes[0].copy()
            
            # Fill missing values from other sources
            for df in dataframes[1:]:
                # Align indices
                df_aligned = df.reindex(combined_df.index)
                # Fill NaN values
                combined_df = combined_df.combine_first(df_aligned)
            
            # Sort by date
            combined_df = combined_df.sort_index()
            
            # Remove duplicates (keep last)
            combined_df = combined_df[~combined_df.index.duplicated(keep='last')]
            
            logger.info(f"✓ {crypto_name}: {len(combined_df)} rows from {len(sources_used)} source(s): {', '.join(sources_used)}")
            return combined_df
        else:
            logger.warning(f"✗ No data found for {crypto_name}")
            return pd.DataFrame()
    
    def collect_all_cryptos(self):
        """
        Collect data for all cryptocurrencies
        """
        logger.info("=" * 60)
        logger.info("CRYPTOCURRENCY DATA COLLECTION")
        logger.info("=" * 60)
        logger.info(f"Date range: {self.start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')}")
        logger.info(f"Output directory: {self.output_dir}")
        logger.info("=" * 60)
        
        results = {}
        failed_cryptos = []
        total_cryptos = len(self.cryptos)
        
        for crypto_name, crypto_info in tqdm(self.cryptos.items(), desc="Collecting Crypto Data"):
            try:
                logger.info(f"\n📊 Processing {crypto_name} ({crypto_info['symbol']}) - {crypto_info['category']}")
                
                # Fetch data
                df = self.fetch_combined(
                    crypto_name=crypto_name,
                    crypto_info=crypto_info,
                    start_date=self.start_date,
                    end_date=self.end_date
                )
                
                if not df.empty:
                    # Save to CSV
                    filename = os.path.join(self.output_dir, f"{crypto_info['symbol']}.csv")
                    df.to_csv(filename)
                    logger.info(f"  ✓ Saved {crypto_name} to {filename} ({len(df)} rows)")
                    results[crypto_info['symbol']] = df
                    
                    # Save metadata
                    self.save_metadata(crypto_name, crypto_info, df)
                else:
                    failed_cryptos.append(crypto_info['symbol'])
                    logger.warning(f"  ✗ No data for {crypto_name}")
                
                # Add delay to avoid rate limiting
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error processing {crypto_name}: {e}")
                failed_cryptos.append(crypto_info['symbol'])
        
        # Save master summary
        self.save_master_summary(results, failed_cryptos)
        
        # Final summary
        logger.info("\n" + "=" * 60)
        logger.info("DATA COLLECTION COMPLETE!")
        logger.info(f"✓ Successfully collected: {len(results)}/{total_cryptos} cryptocurrencies")
        logger.info(f"✗ Failed: {len(failed_cryptos)} cryptocurrencies")
        if failed_cryptos:
            logger.warning(f"Failed: {', '.join(failed_cryptos)}")
        logger.info(f"Output directory: {self.output_dir}")
        logger.info("=" * 60)
        
        return results, failed_cryptos
    
    def save_metadata(self, crypto_name, crypto_info, df):
        """
        Save metadata for a cryptocurrency
        
        Args:
            crypto_name: Name of the cryptocurrency
            crypto_info: Dictionary with crypto information
            df: DataFrame with data
        """
        metadata = {
            'name': crypto_name,
            'symbol': crypto_info['symbol'],
            'category': crypto_info['category'],
            'coingecko_id': crypto_info['coingecko_id'],
            'ccxt_symbol': crypto_info['ccxt_symbol'],
            'yfinance_symbol': crypto_info.get('yfinance_symbol', 'N/A'),
            'start_date': self.start_date.strftime('%Y-%m-%d'),
            'end_date': self.end_date.strftime('%Y-%m-%d'),
            'interval': '1 Day',
            'total_rows': len(df),
            'date_range_start': df.index.min().strftime('%Y-%m-%d'),
            'date_range_end': df.index.max().strftime('%Y-%m-%d'),
            'data_completeness': len(df) / ((self.end_date - self.start_date).days)
        }
        
        metadata_df = pd.DataFrame([metadata])
        filename = os.path.join(self.output_dir, f"{crypto_info['symbol']}_metadata.csv")
        metadata_df.to_csv(filename, index=False)
    
    def save_master_summary(self, results, failed_cryptos):
        """
        Save master summary of all collected data
        """
        summary_data = []
        
        for crypto_name, crypto_info in self.cryptos.items():
            symbol = crypto_info['symbol']
            row = {
                'name': crypto_name,
                'symbol': symbol,
                'category': crypto_info['category'],
                'status': 'Success' if symbol in results else 'Failed',
                'rows': len(results[symbol]) if symbol in results else 0,
                'coingecko_id': crypto_info['coingecko_id'],
                'ccxt_symbol': crypto_info['ccxt_symbol'],
                'yfinance_symbol': crypto_info.get('yfinance_symbol', 'N/A'),
                'date_range_start': self.start_date.strftime('%Y-%m-%d'),
                'date_range_end': self.end_date.strftime('%Y-%m-%d')
            }
            summary_data.append(row)
        
        summary_df = pd.DataFrame(summary_data)
        filename = os.path.join(self.output_dir, 'MASTER_SUMMARY.csv')
        summary_df.to_csv(filename, index=False)
        logger.info(f"\n✓ Saved master summary to {filename}")

def main():
    """
    Main function to run the data collection
    """
    # Configuration
    START_DATE = '2024-01-01'
    END_DATE = '2026-06-22'
    OUTPUT_DIR = 'Crypto'
    
    # Initialize collector
    collector = CryptoDataCollector(
        start_date=START_DATE,
        end_date=END_DATE,
        output_dir=OUTPUT_DIR
    )
    
    # Run collection
    collector.collect_all_cryptos()

if __name__ == "__main__":
    main()