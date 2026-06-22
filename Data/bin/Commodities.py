"""
Commodity Data Collection Script
Combines multiple sources: OilPriceAPI, EIA API, EODHD Commodities API, and USDA NASS API
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
import sys
import subprocess
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
required_packages = ['pandas', 'numpy', 'requests', 'python-dotenv', 'tqdm']
for pkg in required_packages:
    install_package(pkg)

# Import libraries with fallback installation
try:
    from oilpriceapi import OilPriceAPI
except ImportError:
    logger.info("Installing oilpriceapi...")
    os.system('pip install oilpriceapi')
    from oilpriceapi import OilPriceAPI

try:
    from eodhd import APIClient
except ImportError:
    logger.info("Installing eodhd...")
    os.system('pip install eodhd')
    from eodhd import APIClient

try:
    from eia_ng import EIAClient
except ImportError:
    logger.info("Installing eia-ng-client...")
    os.system('pip install eia-ng-client')
    from eia_ng import EIAClient

try:
    import requests
except ImportError:
    logger.info("Installing requests...")
    os.system('pip install requests')
    import requests

class CommodityDataCollector:
    def __init__(self, start_date='2021-01-01', end_date='2026-06-22', output_dir='Commodities'):
        """
        Initialize the commodity data collector
        
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
        
        # Define commodity categories and symbols
        self.commodities = {
            'Energy': {
                'Brent_Crude_Oil': {'codes': ['BRENT', 'BRENT_CRUDE_USD'], 'sources': ['oilpriceapi', 'eodhd']},
                'WTI_Crude_Oil': {'codes': ['WTI', 'WTI_CRUDE_USD'], 'sources': ['oilpriceapi', 'eodhd']},
                'Natural_Gas': {'codes': ['NATURAL_GAS', 'NATURAL_GAS_USD', 'NG'], 'sources': ['oilpriceapi', 'eodhd', 'eia']}
            },
            'Precious_Metals': {
                'Gold': {'codes': ['GOLD', 'XAU'], 'sources': ['eodhd']},
                'Silver': {'codes': ['SILVER', 'XAG'], 'sources': ['eodhd']},
                'Platinum': {'codes': ['PLATINUM', 'XPT'], 'sources': ['eodhd']}
            },
            'Base_Metals': {
                'Copper': {'codes': ['COPPER'], 'sources': ['eodhd']},
                'Aluminum': {'codes': ['ALUMINUM'], 'sources': ['eodhd']},
                'Lead': {'codes': ['LEAD'], 'sources': ['eodhd']}
            },
            'Agriculture': {
                'Wheat': {'codes': ['WHEAT'], 'sources': ['eodhd', 'usda']},
                'Corn': {'codes': ['CORN'], 'sources': ['eodhd', 'usda']},
                'Cotton': {'codes': ['COTTON'], 'sources': ['eodhd', 'usda']},
                'Natural_Rubber': {'codes': ['RUBBER'], 'sources': ['eodhd']}
            },
            'Fertilizers': {
                'Fertilizer_Index': {'codes': ['FERTILIZER'], 'sources': ['eodhd']}
            }
        }
        
        # Initialize API clients
        self.oilpriceapi_client = None
        self.eodhd_client = None
        self.eia_client = None
        self.usda_api_key = None
        
        # Load API keys from environment or config
        self.load_api_keys()
        
        # Initialize clients
        self.initialize_clients()
        
        logger.info("Initialized Commodity Data Collector")
    
    def load_api_keys(self):
        """Load API keys from environment variables"""
        # OilPriceAPI key
        self.oilpriceapi_key = os.getenv('OILPRICEAPI_KEY')
        if not self.oilpriceapi_key:
            logger.warning("OILPRICEAPI_KEY not set. Will use other sources for energy commodities.")
        
        # EODHD API key
        self.eodhd_key = os.getenv('EODHD_API_KEY')
        if not self.eodhd_key:
            logger.warning("EODHD_API_KEY not set. Will use demo key for limited data.")
            self.eodhd_key = 'demo'  # Demo key only works for WTI
        
        # EIA API key
        self.eia_key = os.getenv('EIA_API_KEY')
        if not self.eia_key:
            logger.warning("EIA_API_KEY not set. Natural gas data from EIA will be unavailable.")
        
        # USDA NASS API key
        self.usda_api_key = os.getenv('USDA_NASS_API_KEY')
        if not self.usda_api_key:
            logger.warning("USDA_NASS_API_KEY not set. Agricultural data from USDA will be unavailable.")
    
    def initialize_clients(self):
        """Initialize API clients"""
        try:
            if self.oilpriceapi_key:
                self.oilpriceapi_client = OilPriceAPI(self.oilpriceapi_key)
                logger.info("OilPriceAPI client initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize OilPriceAPI: {e}")
        
        try:
            if self.eodhd_key:
                self.eodhd_client = APIClient(self.eodhd_key)
                logger.info("EODHD client initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize EODHD: {e}")
        
        try:
            if self.eia_key:
                self.eia_client = EIAClient()
                logger.info("EIA client initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize EIA: {e}")
    
    def fetch_from_oilpriceapi(self, commodity_code, start_date, end_date):
        """
        Fetch commodity data from OilPriceAPI
        
        Args:
            commodity_code: Commodity code (e.g., 'BRENT_CRUDE_USD', 'WTI_CRUDE_USD')
            start_date: Start date
            end_date: End date
            
        Returns:
            DataFrame with historical data
        """
        if not self.oilpriceapi_client:
            return pd.DataFrame()
        
        try:
            # Map commodity codes to OilPriceAPI format
            code_mapping = {
                'BRENT': 'BRENT_CRUDE_USD',
                'WTI': 'WTI_CRUDE_USD',
                'NATURAL_GAS': 'NATURAL_GAS_USD'
            }
            
            code = code_mapping.get(commodity_code, commodity_code)
            
            # Get historical data
            df = self.oilpriceapi_client.prices.to_dataframe(
                commodity=code,
                start=start_date.strftime('%Y-%m-%d'),
                end=end_date.strftime('%Y-%m-%d'),
                interval='daily'
            )
            
            if not df.empty:
                # Standardize columns
                df.index = pd.to_datetime(df.index)
                df.columns = ['Close'] if len(df.columns) == 1 else df.columns
                
                # Create OHLC columns if only close price is available
                if len(df.columns) == 1:
                    df['Open'] = df['Close']
                    df['High'] = df['Close']
                    df['Low'] = df['Close']
                    df['Volume'] = 0
                    df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
                
                df.index.name = 'Date'
                logger.debug(f"OilPriceAPI: Retrieved {len(df)} rows for {commodity_code}")
                return df
            
            return pd.DataFrame()
        except Exception as e:
            logger.debug(f"OilPriceAPI failed for {commodity_code}: {e}")
            return pd.DataFrame()
    
    def fetch_from_eodhd(self, commodity_code, start_date, end_date):
        """
        Fetch commodity data from EODHD Commodities API
        
        Args:
            commodity_code: Commodity code (e.g., 'WTI', 'BRENT', 'COPPER', 'WHEAT')
            start_date: Start date
            end_date: End date
            
        Returns:
            DataFrame with historical data
        """
        if not self.eodhd_client:
            return pd.DataFrame()
        
        try:
            # EODHD commodities endpoint
            url = f"https://eodhd.com/api/commodities/historical/{commodity_code}"
            params = {
                'api_token': self.eodhd_key,
                'interval': 'daily',
                'fmt': 'json'
            }
            
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and data['data']:
                    # Convert to DataFrame
                    df = pd.DataFrame(data['data'])
                    df['date'] = pd.to_datetime(df['date'])
                    
                    # Filter by date range
                    mask = (df['date'] >= start_date) & (df['date'] <= end_date)
                    df = df.loc[mask]
                    
                    if not df.empty:
                        df.set_index('date', inplace=True)
                        # EODHD returns 'value' column for commodity prices
                        df['Close'] = df['value']
                        df['Open'] = df['value']
                        df['High'] = df['value']
                        df['Low'] = df['value']
                        df['Volume'] = 0
                        df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
                        df.index.name = 'Date'
                        logger.debug(f"EODHD: Retrieved {len(df)} rows for {commodity_code}")
                        return df
            
            return pd.DataFrame()
        except Exception as e:
            logger.debug(f"EODHD failed for {commodity_code}: {e}")
            return pd.DataFrame()
    
    def fetch_from_eia(self, commodity_code, start_date, end_date):
        """
        Fetch natural gas data from EIA API
        
        Args:
            commodity_code: Commodity code
            start_date: Start date
            end_date: End date
            
        Returns:
            DataFrame with historical data
        """
        if not self.eia_client:
            return pd.DataFrame()
        
        try:
            # Currently supports Natural Gas prices (Henry Hub)
            if commodity_code in ['NATURAL_GAS', 'NG']:
                prices = self.eia_client.natural_gas.spot_prices(
                    start=start_date.strftime('%Y-%m-%d')
                )
                
                if prices:
                    df = pd.DataFrame(prices)
                    if not df.empty and 'date' in df.columns:
                        df['date'] = pd.to_datetime(df['date'])
                        mask = (df['date'] >= start_date) & (df['date'] <= end_date)
                        df = df.loc[mask]
                        
                        if not df.empty:
                            df.set_index('date', inplace=True)
                            if 'price' in df.columns:
                                df['Close'] = df['price']
                                df['Open'] = df['price']
                                df['High'] = df['price']
                                df['Low'] = df['price']
                                df['Volume'] = 0
                                df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
                                df.index.name = 'Date'
                                logger.debug(f"EIA: Retrieved {len(df)} rows for {commodity_code}")
                                return df
            
            return pd.DataFrame()
        except Exception as e:
            logger.debug(f"EIA failed for {commodity_code}: {e}")
            return pd.DataFrame()
    
    def fetch_from_usda(self, commodity_code, start_date, end_date):
        """
        Fetch agricultural data from USDA NASS API
        
        Args:
            commodity_code: Commodity code (e.g., 'WHEAT', 'CORN', 'COTTON')
            start_date: Start date
            end_date: End date
            
        Returns:
            DataFrame with historical data
        """
        if not self.usda_api_key:
            return pd.DataFrame()
        
        try:
            # Map commodity to USDA commodity codes
            commodity_mapping = {
                'WHEAT': {'commodity_desc': 'WHEAT', 'group_desc': 'FIELD CROPS'},
                'CORN': {'commodity_desc': 'CORN', 'group_desc': 'FIELD CROPS'},
                'COTTON': {'commodity_desc': 'COTTON', 'group_desc': 'FIELD CROPS'}
            }
            
            if commodity_code not in commodity_mapping:
                return pd.DataFrame()
            
            params = commodity_mapping[commodity_code]
            
            # USDA NASS QuickStats API
            url = "https://quickstats.nass.usda.gov/api/api_GET/"
            query_params = {
                'key': self.usda_api_key,
                'format': 'JSON',
                'commodity_desc': params['commodity_desc'],
                'group_desc': params['group_desc'],
                'statisticcat_desc': 'PRICE',
                'domain_desc': 'TOTAL',
                'year': f"{start_date.year}:{end_date.year}",
                'agg_level_desc': 'NATIONAL'
            }
            
            response = requests.get(url, params=query_params)
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and data['data']:
                    df = pd.DataFrame(data['data'])
                    
                    if not df.empty and 'Value' in df.columns and 'year' in df.columns:
                        # Aggregate by year
                        df['year'] = pd.to_numeric(df['year'])
                        annual_data = df.groupby('year')['Value'].mean()
                        
                        # Convert to daily frequency (fill with same value for all days in year)
                        date_range = pd.date_range(start_date, end_date, freq='D')
                        daily_data = []
                        
                        for date in date_range:
                            year = date.year
                            if year in annual_data.index:
                                daily_data.append({
                                    'Date': date,
                                    'Close': float(annual_data[year]),
                                    'Open': float(annual_data[year]),
                                    'High': float(annual_data[year]),
                                    'Low': float(annual_data[year]),
                                    'Volume': 0
                                })
                        
                        if daily_data:
                            df = pd.DataFrame(daily_data)
                            df.set_index('Date', inplace=True)
                            logger.debug(f"USDA: Retrieved {len(df)} rows for {commodity_code}")
                            return df
            
            return pd.DataFrame()
        except Exception as e:
            logger.debug(f"USDA failed for {commodity_code}: {e}")
            return pd.DataFrame()
    
    def fetch_commodity_data(self, commodity_name, commodity_codes, sources, start_date, end_date):
        """
        Fetch commodity data from multiple sources and combine
        
        Args:
            commodity_name: Name of the commodity
            commodity_codes: List of codes for this commodity
            sources: List of sources to use
            start_date: Start date
            end_date: End date
            
        Returns:
            Combined DataFrame with data from all sources
        """
        dataframes = []
        sources_used = []
        
        # Try each source for each code
        for code in commodity_codes:
            for source in sources:
                try:
                    df = pd.DataFrame()
                    
                    if source == 'oilpriceapi':
                        df = self.fetch_from_oilpriceapi(code, start_date, end_date)
                    elif source == 'eodhd':
                        df = self.fetch_from_eodhd(code, start_date, end_date)
                    elif source == 'eia':
                        df = self.fetch_from_eia(code, start_date, end_date)
                    elif source == 'usda':
                        df = self.fetch_from_usda(code, start_date, end_date)
                    
                    if not df.empty:
                        dataframes.append(df)
                        sources_used.append(f"{source}:{code}")
                        logger.debug(f"✓ {source}:{code} returned {len(df)} rows for {commodity_name}")
                    
                    # Small delay to avoid rate limiting
                    time.sleep(0.3)
                    
                except Exception as e:
                    logger.debug(f"✗ {source}:{code} failed for {commodity_name}: {e}")
        
        # Combine all data
        if dataframes:
            # Start with the first dataframe
            combined_df = dataframes[0].copy()
            
            # Fill missing values from other sources
            for df in dataframes[1:]:
                # Align indices
                df_aligned = df.reindex(combined_df.index)
                combined_df = combined_df.combine_first(df_aligned)
            
            # Sort by date
            combined_df = combined_df.sort_index()
            
            logger.info(f"✓ Collected {len(combined_df)} rows for {commodity_name} from {len(sources_used)} source(s)")
            return combined_df
        else:
            logger.warning(f"✗ No data found for {commodity_name}")
            return pd.DataFrame()
    
    def collect_all_commodities(self):
        """
        Collect data for all commodities
        """
        logger.info("=" * 60)
        logger.info("COMMODITY DATA COLLECTION")
        logger.info("=" * 60)
        logger.info(f"Date range: {self.start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')}")
        logger.info(f"Output directory: {self.output_dir}")
        logger.info("=" * 60)
        
        results = {}
        failed_commodities = []
        total_commodities = sum(len(items) for items in self.commodities.values())
        processed = 0
        
        for category, commodities in self.commodities.items():
            logger.info(f"\n📁 Category: {category}")
            
            for commodity_name, commodity_info in tqdm(commodities.items(), desc=f"{category}"):
                try:
                    # Fetch data
                    df = self.fetch_commodity_data(
                        commodity_name=commodity_name,
                        commodity_codes=commodity_info['codes'],
                        sources=commodity_info['sources'],
                        start_date=self.start_date,
                        end_date=self.end_date
                    )
                    
                    if not df.empty:
                        # Save to CSV
                        filename = os.path.join(self.output_dir, f"{commodity_name}.csv")
                        df.to_csv(filename)
                        logger.info(f"  ✓ Saved {commodity_name} to {filename} ({len(df)} rows)")
                        results[commodity_name] = df
                    else:
                        failed_commodities.append(commodity_name)
                        logger.warning(f"  ✗ No data for {commodity_name}")
                    
                    processed += 1
                    
                    # Add delay between commodities
                    time.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error processing {commodity_name}: {e}")
                    failed_commodities.append(commodity_name)
                    processed += 1
        
        # Save master summary
        self.save_master_summary(results, failed_commodities)
        
        # Final summary
        logger.info("\n" + "=" * 60)
        logger.info("DATA COLLECTION COMPLETE!")
        logger.info(f"✓ Successfully collected: {len(results)}/{total_commodities} commodities")
        logger.info(f"✗ Failed: {len(failed_commodities)} commodities")
        if failed_commodities:
            logger.warning(f"Failed: {', '.join(failed_commodities[:10])}")
        logger.info(f"Output directory: {self.output_dir}")
        logger.info("=" * 60)
        
        return results, failed_commodities
    
    def save_master_summary(self, results, failed_commodities):
        """
        Save master summary of all collected data
        """
        summary_data = []
        
        for category, commodities in self.commodities.items():
            for commodity_name, commodity_info in commodities.items():
                row = {
                    'category': category,
                    'commodity': commodity_name,
                    'codes': ', '.join(commodity_info['codes']),
                    'sources': ', '.join(commodity_info['sources']),
                    'status': 'Success' if commodity_name in results else 'Failed',
                    'rows': len(results[commodity_name]) if commodity_name in results else 0,
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
    START_DATE = '2021-01-01'
    END_DATE = '2026-06-22'
    OUTPUT_DIR = 'Commodities'
    
    # Initialize collector
    collector = CommodityDataCollector(
        start_date=START_DATE,
        end_date=END_DATE,
        output_dir=OUTPUT_DIR
    )
    
    # Run collection
    collector.collect_all_commodities()

if __name__ == "__main__":
    main()