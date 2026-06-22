"""
Data Collection Script for US ETFs
Combines yfinance, Alpha Vantage, and pandas_datareader for maximum reliability
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import logging
from tqdm import tqdm
import warnings
warnings.filterwarnings('ignore')

# Import libraries
try:
    import yfinance as yf
except ImportError:
    print("Installing yfinance...")
    os.system('pip install yfinance')
    import yfinance as yf

try:
    from alpha_vantage.timeseries import TimeSeries
except ImportError:
    print("Installing alpha_vantage...")
    os.system('pip install alpha-vantage')
    from alpha_vantage.timeseries import TimeSeries

try:
    import pandas_datareader as pdr
    from pandas_datareader import data as web
except ImportError:
    print("Installing pandas_datareader...")
    os.system('pip install pandas-datareader')
    import pandas_datareader as pdr
    from pandas_datareader import data as web

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class USETFDataCollector:
    def __init__(self, start_date='2021-01-01', end_date='2026-06-22', output_dir='ETF', alpha_vantage_key=None):
        """
        Initialize the data collector for US ETFs
        
        Args:
            start_date: Start date for data collection
            end_date: End date for data collection
            output_dir: Directory to save CSV files
            alpha_vantage_key: Alpha Vantage API key (free tier available)
        """
        self.start_date = datetime.strptime(start_date, '%Y-%m-%d')
        self.end_date = datetime.strptime(end_date, '%Y-%m-%d')
        self.output_dir = output_dir
        
        # ETF definitions with full names
        self.etfs = {
            'SPY': {'name': 'SPDR S&P 500 ETF', 'category': 'Large Cap'},
            'QQQ': {'name': 'Invesco QQQ Trust', 'category': 'Large Cap'},
            'IVV': {'name': 'iShares Core S&P 500 ETF', 'category': 'Large Cap'},
            'XLK': {'name': 'Technology Select Sector SPDR', 'category': 'Sector'},
            'XLE': {'name': 'Energy Select Sector SPDR', 'category': 'Sector'},
            'XLV': {'name': 'Health Care Select Sector SPDR', 'category': 'Sector'},
            'AGG': {'name': 'iShares Core U.S. Aggregate Bond ETF', 'category': 'Fixed Income'},
            'LQD': {'name': 'iShares iBoxx Investment Grade Corporate Bond ETF', 'category': 'Fixed Income'},
            'TLT': {'name': 'iShares 20+ Year Treasury Bond ETF', 'category': 'Fixed Income'},
            'GLD': {'name': 'SPDR Gold Shares', 'category': 'Commodity'},
            'USO': {'name': 'United States Oil Fund', 'category': 'Commodity'},
            'EFA': {'name': 'iShares MSCI EAFE ETF', 'category': 'International'},
            'EEM': {'name': 'iShares MSCI Emerging Markets ETF', 'category': 'International'},
            'EWY': {'name': 'iShares MSCI South Korea ETF', 'category': 'International'},
            'IBIT': {'name': 'iShares Bitcoin Trust', 'category': 'Alternatives'}
        }
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize Alpha Vantage
        self.alpha_vantage_key = alpha_vantage_key or os.getenv('ALPHA_VANTAGE_API_KEY')
        self.alpha_vantage_client = None
        if self.alpha_vantage_key:
            try:
                self.alpha_vantage_client = TimeSeries(key=self.alpha_vantage_key, output_format='pandas')
                logger.info("Alpha Vantage initialized successfully")
            except Exception as e:
                logger.warning(f"Alpha Vantage initialization failed: {e}")
        else:
            logger.info("No Alpha Vantage API key provided. Will use yfinance and pandas_datareader.")
        
        # Rate limiting tracking
        self.alpha_vantage_last_call = None
        self.alpha_vantage_call_count = 0
        
    def fetch_data_yfinance(self, symbol, start_date, end_date):
        """
        Fetch historical data using yfinance
        
        Args:
            symbol: ETF ticker symbol
            start_date: Start date
            end_date: End date
            
        Returns:
            DataFrame with OHLCV data
        """
        try:
            df = yf.download(symbol, start=start_date, end=end_date, progress=False, auto_adjust=True)
            
            if not df.empty:
                # yfinance returns columns in different formats, standardize
                if 'Adj Close' in df.columns and 'Close' not in df.columns:
                    df['Close'] = df['Adj Close']
                elif 'Close' in df.columns and 'Adj Close' not in df.columns:
                    df['Adj Close'] = df['Close']
                
                # Ensure we have standard OHLCV columns
                required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
                for col in required_cols:
                    if col not in df.columns:
                        if col == 'Volume':
                            df[col] = 0
                        else:
                            df[col] = df['Close']  # Use Close as fallback
                
                df.index.name = 'Date'
                return df[required_cols]
            return pd.DataFrame()
        except Exception as e:
            logger.debug(f"yfinance failed for {symbol}: {e}")
            return pd.DataFrame()
    
    def fetch_data_alpha_vantage(self, symbol, start_date, end_date):
        """
        Fetch historical data using Alpha Vantage
        
        Args:
            symbol: ETF ticker symbol
            start_date: Start date
            end_date: End date
            
        Returns:
            DataFrame with OHLCV data
        """
        if not self.alpha_vantage_client:
            return pd.DataFrame()
        
        try:
            # Rate limiting: Free tier allows 5 calls per minute
            if self.alpha_vantage_last_call:
                time_since_last = (datetime.now() - self.alpha_vantage_last_call).total_seconds()
                if time_since_last < 12:  # 60/5 = 12 seconds between calls
                    time.sleep(12 - time_since_last)
            
            # Get daily data
            data, meta_data = self.alpha_vantage_client.get_daily(symbol=symbol, outputsize='full')
            
            self.alpha_vantage_last_call = datetime.now()
            self.alpha_vantage_call_count += 1
            
            if not data.empty:
                # Alpha Vantage returns '1. open', '2. high', etc.
                data.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
                data.index = pd.to_datetime(data.index)
                
                # Filter by date range
                mask = (data.index >= start_date) & (data.index <= end_date)
                data = data.loc[mask]
                
                if not data.empty:
                    data.index.name = 'Date'
                    return data[['Open', 'High', 'Low', 'Close', 'Volume']]
            
            return pd.DataFrame()
        except Exception as e:
            logger.debug(f"Alpha Vantage failed for {symbol}: {e}")
            return pd.DataFrame()
    
    def fetch_data_pandas_datareader(self, symbol, start_date, end_date):
        """
        Fetch historical data using pandas_datareader (using Yahoo Finance as data source)
        
        Args:
            symbol: ETF ticker symbol
            start_date: Start date
            end_date: End date
            
        Returns:
            DataFrame with OHLCV data
        """
        try:
            # Use Yahoo Finance through pandas_datareader
            df = web.DataReader(symbol, 'yahoo', start_date, end_date)
            
            if not df.empty:
                # Standardize columns
                df.columns = ['High', 'Low', 'Open', 'Close', 'Volume', 'Adj Close']
                if 'Adj Close' in df.columns:
                    df['Close'] = df['Adj Close']
                
                df.index.name = 'Date'
                return df[['Open', 'High', 'Low', 'Close', 'Volume']]
            return pd.DataFrame()
        except Exception as e:
            logger.debug(f"pandas_datareader failed for {symbol}: {e}")
            return pd.DataFrame()
    
    def fetch_data_combined(self, symbol, start_date, end_date):
        """
        Fetch data using multiple sources, combining for maximum coverage
        
        Args:
            symbol: ETF ticker symbol
            start_date: Start date
            end_date: End date
            
        Returns:
            DataFrame with combined OHLCV data
        """
        # Try sources in order of preference
        dataframes = []
        source_used = []
        
        # Try yfinance first (most reliable for US ETFs)
        df1 = self.fetch_data_yfinance(symbol, start_date, end_date)
        if not df1.empty:
            dataframes.append(df1)
            source_used.append('yfinance')
        
        # Try pandas_datareader second
        df2 = self.fetch_data_pandas_datareader(symbol, start_date, end_date)
        if not df2.empty:
            dataframes.append(df2)
            source_used.append('pandas_datareader')
        
        # Try Alpha Vantage last (due to rate limits)
        df3 = self.fetch_data_alpha_vantage(symbol, start_date, end_date)
        if not df3.empty:
            dataframes.append(df3)
            source_used.append('alpha_vantage')
        
        # Combine all dataframes
        if dataframes:
            # Start with the first dataframe
            combined_df = dataframes[0].copy()
            
            # Fill missing values from other sources
            for df in dataframes[1:]:
                # Align indices
                df_aligned = df.reindex(combined_df.index)
                # Fill NaN values
                combined_df = combined_df.combine_first(df_aligned)
            
            logger.debug(f"Combined data for {symbol} from sources: {', '.join(source_used)}")
            return combined_df
        else:
            logger.warning(f"No data found for {symbol} from any source")
            return pd.DataFrame()
    
    def validate_data(self, df, symbol):
        """
        Validate the collected data for quality
        
        Args:
            df: DataFrame to validate
            symbol: ETF ticker symbol
            
        Returns:
            Boolean indicating if data is valid
        """
        if df.empty:
            return False
        
        # Check for required columns
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        if not all(col in df.columns for col in required_cols):
            logger.warning(f"Missing columns in {symbol} data")
            return False
        
        # Check for reasonable date range coverage
        expected_days = (self.end_date - self.start_date).days
        actual_days = len(df)
        coverage_ratio = actual_days / expected_days
        
        # Accept if we have at least 60% coverage
        if coverage_ratio < 0.6:
            logger.warning(f"Low coverage for {symbol}: {coverage_ratio:.1%}")
            return False
        
        # Check for extreme outliers
        for col in ['Open', 'High', 'Low', 'Close']:
            if df[col].std() == 0:
                logger.warning(f"Zero variance in {symbol} for column {col}")
                return False
        
        return True
    
    def collect_etf_data(self, symbol, etf_info):
        """
        Collect data for a single ETF
        
        Args:
            symbol: ETF ticker symbol
            etf_info: Dictionary with ETF information
            
        Returns:
            DataFrame with collected data, or None if failed
        """
        logger.info(f"Collecting data for {symbol} ({etf_info['name']})")
        
        try:
            df = self.fetch_data_combined(symbol, self.start_date, self.end_date)
            
            if not df.empty and self.validate_data(df, symbol):
                logger.info(f"✓ Successfully collected {len(df)} rows for {symbol}")
                return df
            else:
                logger.warning(f"✗ Data validation failed for {symbol}")
                return None
                
        except Exception as e:
            logger.error(f"✗ Failed to collect data for {symbol}: {e}")
            return None
    
    def save_etf_data(self, symbol, df, etf_info):
        """
        Save ETF data to CSV with metadata
        
        Args:
            symbol: ETF ticker symbol
            df: DataFrame with OHLCV data
            etf_info: Dictionary with ETF information
        """
        if df is None or df.empty:
            logger.warning(f"No data to save for {symbol}")
            return
        
        # Prepare data for saving
        df_copy = df.copy()
        
        # Ensure all columns are present
        for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
            if col not in df_copy.columns:
                if col == 'Volume':
                    df_copy[col] = 0
                else:
                    df_copy[col] = df_copy['Close'] if 'Close' in df_copy.columns else np.nan
        
        # Sort by date
        df_copy = df_copy.sort_index()
        
        # Save main data
        filename = os.path.join(self.output_dir, f"{symbol}.csv")
        df_copy.to_csv(filename)
        logger.info(f"Saved {symbol} data to {filename}")
        
        # Save metadata
        metadata = {
            'symbol': symbol,
            'name': etf_info['name'],
            'category': etf_info['category'],
            'start_date': self.start_date.strftime('%Y-%m-%d'),
            'end_date': self.end_date.strftime('%Y-%m-%d'),
            'interval': '1 Day',
            'total_rows': len(df_copy),
            'date_range': f"{df_copy.index.min()} to {df_copy.index.max()}",
            'has_data': True,
            'data_completeness': len(df_copy) / ((self.end_date - self.start_date).days)
        }
        
        metadata_df = pd.DataFrame([metadata])
        metadata_filename = os.path.join(self.output_dir, f"{symbol}_metadata.csv")
        metadata_df.to_csv(metadata_filename, index=False)
        logger.info(f"Saved {symbol} metadata to {metadata_filename}")
    
    def collect_all_etfs(self):
        """
        Collect data for all ETFs
        """
        results = {}
        failed_symbols = []
        success_count = 0
        
        total_etfs = len(self.etfs)
        logger.info(f"Starting collection for {total_etfs} ETFs")
        logger.info("=" * 60)
        
        for symbol, etf_info in tqdm(self.etfs.items(), desc="Collecting ETFs"):
            try:
                # Collect data
                df = self.collect_etf_data(symbol, etf_info)
                
                if df is not None:
                    # Save data
                    self.save_etf_data(symbol, df, etf_info)
                    results[symbol] = df
                    success_count += 1
                else:
                    failed_symbols.append(symbol)
                
                # Add delay between requests to avoid rate limiting
                if len(self.etfs) > 1:
                    time.sleep(1)  # 1 second delay between ETFs
                    
            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}")
                failed_symbols.append(symbol)
        
        # Final summary
        logger.info("\n" + "=" * 60)
        logger.info("DATA COLLECTION COMPLETE!")
        logger.info(f"✓ Successfully collected: {success_count}/{total_etfs} ETFs")
        logger.info(f"✗ Failed: {len(failed_symbols)} ETFs")
        
        if failed_symbols:
            logger.warning(f"Failed symbols: {', '.join(failed_symbols)}")
        
        # Save a master summary file
        self.save_master_summary(results, failed_symbols)
        
        return results, failed_symbols
    
    def save_master_summary(self, results, failed_symbols):
        """
        Save a master summary file with information about all collected ETFs
        
        Args:
            results: Dictionary with successful symbols and their DataFrames
            failed_symbols: List of symbols that failed
        """
        summary_data = []
        
        for symbol, etf_info in self.etfs.items():
            row = {
                'symbol': symbol,
                'name': etf_info['name'],
                'category': etf_info['category'],
                'status': 'Success' if symbol in results else 'Failed',
                'rows': len(results[symbol]) if symbol in results else 0,
                'date_range_start': self.start_date.strftime('%Y-%m-%d'),
                'date_range_end': self.end_date.strftime('%Y-%m-%d')
            }
            summary_data.append(row)
        
        summary_df = pd.DataFrame(summary_data)
        summary_filename = os.path.join(self.output_dir, 'MASTER_SUMMARY.csv')
        summary_df.to_csv(summary_filename, index=False)
        logger.info(f"Saved master summary to {summary_filename}")
    
    def get_data_quality_report(self):
        """
        Generate a data quality report for all collected ETFs
        """
        logger.info("\n" + "=" * 60)
        logger.info("DATA QUALITY REPORT")
        logger.info("=" * 60)
        
        for symbol, etf_info in self.etfs.items():
            filename = os.path.join(self.output_dir, f"{symbol}.csv")
            if os.path.exists(filename):
                df = pd.read_csv(filename, index_col=0, parse_dates=True)
                expected_days = (self.end_date - self.start_date).days
                actual_days = len(df)
                coverage = actual_days / expected_days * 100
                
                logger.info(f"{symbol} ({etf_info['category']}):")
                logger.info(f"  Rows: {actual_days:,}")
                logger.info(f"  Coverage: {coverage:.1f}%")
                logger.info(f"  Date range: {df.index.min()} to {df.index.max()}")
                logger.info("")
            else:
                logger.warning(f"{symbol}: Data file not found")

def main():
    """
    Main function to run the data collection
    """
    # Configuration
    START_DATE = '2021-01-01'
    END_DATE = '2026-06-22'
    OUTPUT_DIR = 'ETF'
    
    # Optional: Add your Alpha Vantage API key (free tier)
    ALPHA_VANTAGE_KEY = None  # Set your key here or as environment variable
    
    # Initialize collector
    collector = USETFDataCollector(
        start_date=START_DATE,
        end_date=END_DATE,
        output_dir=OUTPUT_DIR,
        alpha_vantage_key=ALPHA_VANTAGE_KEY
    )
    
    # Print ETFs to collect
    logger.info("=" * 60)
    logger.info("US ETF DATA COLLECTOR")
    logger.info("=" * 60)
    logger.info(f"Date range: {START_DATE} to {END_DATE}")
    logger.info(f"Output directory: {OUTPUT_DIR}")
    logger.info(f"Total ETFs: {len(collector.etfs)}")
    logger.info("\nETFs to collect:")
    for symbol, info in collector.etfs.items():
        logger.info(f"  {symbol} - {info['name']} ({info['category']})")
    logger.info("=" * 60 + "\n")
    
    # Start collection
    results, failed = collector.collect_all_etfs()
    
    # Show quality report
    collector.get_data_quality_report()
    
    # Final summary
    logger.info("\n" + "=" * 60)
    logger.info("✅ COLLECTION COMPLETE!")
    logger.info(f"Output folder: {OUTPUT_DIR}")
    logger.info(f"Files created: {len(results)} ETF CSV files + metadata")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()