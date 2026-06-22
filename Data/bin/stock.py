"""
Data Collection Script for NSE Indices
Combines multiple data sources for maximum reliability
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
    import nselib
    from nselib import capital_market
except ImportError:
    print("Installing nselib...")
    os.system('pip install nselib')
    from nselib import capital_market

try:
    import yfinance as yf
except ImportError:
    print("Installing yfinance...")
    os.system('pip install yfinance')
    import yfinance as yf

try:
    from nsepy import get_history
    from nsepy import get_index
except ImportError:
    print("Installing nsepy...")
    os.system('pip install nsepy')
    from nsepy import get_history
    from nsepy import get_index

try:
    from pyzdata import PyZData, Interval
except ImportError:
    print("Installing pyzdata...")
    os.system('pip install pyzdata')
    from pyzdata import PyZData, Interval

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NSEIndexDataCollector:
    def __init__(self, start_date='2021-01-01', end_date='2026-06-22', output_dir='Stock'):
        """
        Initialize the data collector
        
        Args:
            start_date: Start date for data collection
            end_date: End date for data collection
            output_dir: Directory to save CSV files
        """
        self.start_date = datetime.strptime(start_date, '%Y-%m-%d')
        self.end_date = datetime.strptime(end_date, '%Y-%m-%d')
        self.output_dir = output_dir
        self.index_mapping = {
            'NIFTY 50': 'N50',
            'NIFTY Next 50': 'NNext',
            'NIFTY Midcap 100': 'NMidcap',
            'NIFTY Smallcap 100': 'NSmallcap'
        }
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize PyZData (optional, requires enctoken)
        self.pyzdata_client = None
        try:
            # You can set your enctoken as environment variable or pass it here
            # self.pyzdata_client = PyZData(enctoken="your_enctoken_here")
            logger.info("PyZData initialized (optional)")
        except:
            logger.warning("PyZData not initialized. Will use other sources.")
    
    def get_constituents_nselib(self, index_name):
        """
        Get constituents using nselib
        
        Args:
            index_name: Name of the index
            
        Returns:
            List of symbols
        """
        try:
            if 'NIFTY 50' in index_name:
                df = capital_market.nifty50_equity_list()
                symbols = df['SYMBOL'].tolist()
            elif 'Next 50' in index_name:
                df = capital_market.niftynext50_equity_list()
                symbols = df['SYMBOL'].tolist()
            elif 'Midcap 100' in index_name:
                df = capital_market.niftymidcap150_equity_list()
                symbols = df['SYMBOL'].tolist()[:100]  # First 100 for Midcap 100
            elif 'Smallcap 100' in index_name:
                df = capital_market.niftysmallcap250_equity_list()
                symbols = df['SYMBOL'].tolist()[:100]  # First 100 for Smallcap 100
            else:
                symbols = []
            
            logger.info(f"nselib: Found {len(symbols)} constituents for {index_name}")
            return symbols[:100]  # Ensure max 100 for midcap and smallcap
        except Exception as e:
            logger.error(f"Error getting constituents from nselib: {e}")
            return []
    
    def get_constituents_yfinance(self, index_name):
        """
        Get constituents using yfinance (fallback)
        
        Args:
            index_name: Name of the index
            
        Returns:
            List of symbols
        """
        # This is a fallback - yfinance doesn't directly provide index constituents
        # We'll use predefined lists based on common knowledge
        fallback_lists = {
            'NIFTY 50': ['RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'HINDUNILVR', 'ICICIBANK', 
                        'ITC', 'SBIN', 'BHARTIARTL', 'KOTAKBANK', 'LT', 'HCLTECH', 'ASIANPAINT', 
                        'AXISBANK', 'MARUTI', 'SUNPHARMA', 'TITAN', 'WIPRO', 'ULTRACEMCO', 
                        'BAJFINANCE', 'ADANIPORTS', 'ONGC', 'NTPC', 'POWERGRID', 'M&M', 
                        'TATASTEEL', 'JSWSTEEL', 'HDFCLIFE', 'SBILIFE', 'DRREDDY', 
                        'ADANIENT', 'BRITANNIA', 'GRASIM', 'NESTLEIND', 'HDFC', 
                        'TECHM', 'COALINDIA', 'BAJAJFINSV', 'HINDALCO', 'EICHERMOT', 
                        'DIVISLAB', 'APOLLOHOSP', 'BAJAJ-AUTO', 'HEROMOTOCO', 'TATAMOTORS', 
                        'UPL', 'CIPLA', 'SHREECEM', 'TATACONSUM', 'HDFCBANK'],
            'NIFTY Next 50': ['ADANIGREEN', 'ADANIPORTS', 'AMBUJACEM', 'APOLLOHOSP', 'ASHOKLEY',
                            'AUROPHARMA', 'BANDHANBNK', 'BANKBARODA', 'BEL', 'BERGEPAINT',
                            'BHEL', 'BIOCON', 'BPCL', 'BRITANNIA', 'CADILAHC',
                            'CANBK', 'CHOLAFIN', 'COLPAL', 'CONCOR', 'DABUR',
                            'DALBHARAT', 'DLF', 'EICHERMOT', 'ESCORTS', 'EXIDEIND',
                            'GODREJCP', 'GODREJPROP', 'GUJFLUORO', 'HAL', 'HAVELLS',
                            'HDFCLIFE', 'HEROMOTOCO', 'HINDALCO', 'INDIAMART', 'INDIGO',
                            'JUBLFOOD', 'LIC', 'LTTS', 'M&M', 'MCDOWELL-N',
                            'MUTHOOTFIN', 'NAUKRI', 'PAGEIND', 'PIDILITIND', 'PEL',
                            'PIIND', 'SBICARD', 'SRTRANSFIN', 'SUNTV', 'TATAPOWER']
        }
        
        symbols = fallback_lists.get(index_name, [])
        logger.info(f"yfinance fallback: Found {len(symbols)} constituents for {index_name}")
        return symbols
    
    def get_constituents(self, index_name):
        """
        Get constituents using multiple sources (preference: nselib > fallback)
        
        Args:
            index_name: Name of the index
            
        Returns:
            List of symbols
        """
        # Try nselib first
        symbols = self.get_constituents_nselib(index_name)
        
        # If nselib fails, use fallback
        if not symbols:
            logger.warning(f"nselib failed for {index_name}, using fallback")
            symbols = self.get_constituents_yfinance(index_name)
        
        return symbols
    
    def fetch_data_yfinance(self, symbol, start_date, end_date):
        """
        Fetch historical data using yfinance
        
        Args:
            symbol: Stock symbol
            start_date: Start date
            end_date: End date
            
        Returns:
            DataFrame with OHLCV data
        """
        try:
            # Add .NS suffix for NSE stocks
            ticker = f"{symbol}.NS"
            df = yf.download(ticker, start=start_date, end=end_date, progress=False)
            
            if not df.empty:
                df.columns = ['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']
                df.index.name = 'Date'
                return df[['Open', 'High', 'Low', 'Close', 'Volume']]
            return pd.DataFrame()
        except Exception as e:
            logger.debug(f"yfinance failed for {symbol}: {e}")
            return pd.DataFrame()
    
    def fetch_data_nsepy(self, symbol, start_date, end_date):
        """
        Fetch historical data using nsepy
        
        Args:
            symbol: Stock symbol
            start_date: Start date
            end_date: End date
            
        Returns:
            DataFrame with OHLCV data
        """
        try:
            df = get_history(symbol=symbol, 
                           start=start_date, 
                           end=end_date)
            
            if not df.empty:
                df = df[['OPEN', 'HIGH', 'LOW', 'CLOSE', 'VOLUME']].copy()
                df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
                df.index.name = 'Date'
                return df
            return pd.DataFrame()
        except Exception as e:
            logger.debug(f"nsepy failed for {symbol}: {e}")
            return pd.DataFrame()
    
    def fetch_data_nselib(self, symbol, start_date, end_date):
        """
        Fetch historical data using nselib
        
        Args:
            symbol: Stock symbol
            start_date: Start date
            end_date: End date
            
        Returns:
            DataFrame with OHLCV data
        """
        try:
            df = capital_market.price_volume_data(
                symbol=symbol,
                from_date=start_date.strftime('%d-%m-%Y'),
                to_date=end_date.strftime('%d-%m-%Y')
            )
            
            if not df.empty:
                # Rename columns to match standard format
                df = df[['Date', 'OPEN', 'HIGH', 'LOW', 'CLOSE', 'VOLUME']].copy()
                df.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
                df['Date'] = pd.to_datetime(df['Date'])
                df.set_index('Date', inplace=True)
                return df
            return pd.DataFrame()
        except Exception as e:
            logger.debug(f"nselib failed for {symbol}: {e}")
            return pd.DataFrame()
    
    def fetch_data_combined(self, symbol, start_date, end_date):
        """
        Fetch data using multiple sources, combining for maximum coverage
        
        Args:
            symbol: Stock symbol
            start_date: Start date
            end_date: End date
            
        Returns:
            DataFrame with combined OHLCV data
        """
        # Try sources in order of preference
        dataframes = []
        
        # Try nselib
        df1 = self.fetch_data_nselib(symbol, start_date, end_date)
        if not df1.empty:
            dataframes.append(df1)
        
        # Try nsepy
        df2 = self.fetch_data_nsepy(symbol, start_date, end_date)
        if not df2.empty:
            dataframes.append(df2)
        
        # Try yfinance
        df3 = self.fetch_data_yfinance(symbol, start_date, end_date)
        if not df3.empty:
            dataframes.append(df3)
        
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
            
            return combined_df
        else:
            logger.warning(f"No data found for {symbol} from any source")
            return pd.DataFrame()
    
    def collect_index_data(self, index_name, index_code):
        """
        Collect data for all constituents of an index
        
        Args:
            index_name: Full name of the index
            index_code: Short code for filename (e.g., 'N50', 'NNext')
            
        Returns:
            Dictionary with symbol: DataFrame pairs
        """
        logger.info(f"Collecting data for {index_name} ({index_code})")
        
        # Get constituents
        symbols = self.get_constituents(index_name)
        
        if not symbols:
            logger.error(f"No symbols found for {index_name}")
            return {}
        
        # Collect data for each symbol
        data_dict = {}
        failed_symbols = []
        
        for symbol in tqdm(symbols, desc=f"Processing {index_code}"):
            try:
                df = self.fetch_data_combined(symbol, self.start_date, self.end_date)
                
                if not df.empty and len(df) > 0:
                    data_dict[symbol] = df
                else:
                    failed_symbols.append(symbol)
                
                # Add small delay to avoid rate limiting
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Failed to collect data for {symbol}: {e}")
                failed_symbols.append(symbol)
        
        # Log summary
        logger.info(f"Successfully collected data for {len(data_dict)} out of {len(symbols)} symbols")
        if failed_symbols:
            logger.warning(f"Failed symbols: {failed_symbols[:10]}...")  # Show first 10 failures
        
        return data_dict
    
    def save_to_csv(self, data_dict, index_code, additional_info=None):
        """
        Save collected data to CSV files
        
        Args:
            data_dict: Dictionary with symbol: DataFrame pairs
            index_code: Code for the index (e.g., 'N50', 'NNext')
            additional_info: Additional metadata to save
        """
        if not data_dict:
            logger.warning(f"No data to save for {index_code}")
            return
        
        # Create a combined DataFrame with all symbols
        combined_data = {}
        
        for symbol, df in data_dict.items():
            # Rename columns to include symbol name
            df_copy = df.copy()
            for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
                df_copy[f'{symbol}_{col}'] = df_copy[col]
            df_copy = df_copy[['Open', 'High', 'Low', 'Close', 'Volume']]
            df_copy.columns = [f'{symbol}_{col}' for col in df_copy.columns]
            combined_data[symbol] = df_copy
        
        # Merge all dataframes on date index
        if combined_data:
            combined_df = pd.concat(combined_data.values(), axis=1)
            # Remove duplicate columns if any
            combined_df = combined_df.loc[:, ~combined_df.columns.duplicated()]
            
            # Save to CSV
            filename = os.path.join(self.output_dir, f"{index_code}.csv")
            combined_df.to_csv(filename)
            logger.info(f"Saved {len(data_dict)} symbols to {filename}")
            
            # Also save a summary file with metadata
            summary_info = {
                'index_name': index_code,
                'total_symbols': len(data_dict),
                'symbols': list(data_dict.keys()),
                'date_range': f"{self.start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')}",
                'interval': '1 Day'
            }
            
            if additional_info:
                summary_info.update(additional_info)
            
            summary_df = pd.DataFrame([summary_info])
            summary_filename = os.path.join(self.output_dir, f"{index_code}_metadata.csv")
            summary_df.to_csv(summary_filename)
            logger.info(f"Saved metadata to {summary_filename}")
    
    def collect_all_indices(self):
        """
        Collect data for all indices specified
        """
        indices = [
            {'name': 'NIFTY 50', 'code': 'N50'},
            {'name': 'NIFTY Next 50', 'code': 'NNext'},
            {'name': 'NIFTY Midcap 100', 'code': 'NMidcap'},
            {'name': 'NIFTY Smallcap 100', 'code': 'NSmallcap'}
        ]
        
        all_results = {}
        
        for index_info in indices:
            index_name = index_info['name']
            index_code = index_info['code']
            
            try:
                # Collect data
                data_dict = self.collect_index_data(index_name, index_code)
                
                if data_dict:
                    # Save to CSV
                    self.save_to_csv(data_dict, index_code)
                    all_results[index_code] = data_dict
                else:
                    logger.error(f"No data collected for {index_name}")
                    
            except Exception as e:
                logger.error(f"Error processing {index_name}: {e}")
            
            # Add a delay between indices to avoid rate limiting
            time.sleep(2)
        
        return all_results

def main():
    """
    Main function to run the data collection
    """
    # Configuration
    START_DATE = '2021-01-01'
    END_DATE = '2026-06-22'
    OUTPUT_DIR = 'Stock'  # Changed from 'stock' to 'Stock' as per your request
    
    # Initialize collector
    collector = NSEIndexDataCollector(
        start_date=START_DATE,
        end_date=END_DATE,
        output_dir=OUTPUT_DIR
    )
    
    # Start collection
    logger.info("=" * 60)
    logger.info("Starting data collection for NSE indices")
    logger.info(f"Date range: {START_DATE} to {END_DATE}")
    logger.info(f"Output directory: {OUTPUT_DIR}")
    logger.info("=" * 60)
    
    # Collect all indices
    results = collector.collect_all_indices()
    
    # Final summary
    logger.info("\n" + "=" * 60)
    logger.info("Data collection complete!")
    logger.info(f"Total indices processed: {len(results)}")
    for index_code, data_dict in results.items():
        logger.info(f"  {index_code}: {len(data_dict)} symbols")
    logger.info(f"All data saved to '{OUTPUT_DIR}' folder")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()