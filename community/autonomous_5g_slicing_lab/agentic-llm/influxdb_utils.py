"""
InfluxDB client utility for 5G network metrics
"""
import os
import time
from datetime import datetime
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import logging

logger = logging.getLogger(__name__)

class InfluxDBMetricsClient:
    def __init__(self, url="http://localhost:9001", token="5g-lab-token", 
                 org="5g-lab", bucket="5g-metrics"):
        """
        Initialize InfluxDB client for metrics storage
        
        Args:
            url (str): InfluxDB server URL
            token (str): Authentication token
            org (str): Organization name
            bucket (str): Bucket name for storing metrics
        """
        self.url = url
        self.token = token
        self.org = org
        self.bucket = bucket
        self.client = None
        self.write_api = None
        
    def connect(self):
        """Establish connection to InfluxDB"""
        try:
            self.client = InfluxDBClient(
                url=self.url,
                token=self.token,
                org=self.org
            )
            self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
            logger.info("Successfully connected to InfluxDB")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to InfluxDB: {e}")
            return False
    
    def write_metrics(self, ue: str, loss_percentage: float, bitrate: float, timestamp: datetime = None):
        """
        Write network metrics to InfluxDB
        
        Args:
            ue (str): User Equipment identifier
            loss_percentage (float): Packet loss percentage
            bitrate (float): Transfer rate in MBytes
            timestamp (datetime): Timestamp for the measurement
        """
        if not self.write_api:
            logger.error("InfluxDB client not connected")
            return False
            
        try:
            if timestamp is None:
                timestamp = datetime.utcnow()
                
            # Create data points
            loss_point = Point("network_metrics") \
                .tag("ue", ue) \
                .field("loss_percentage", loss_percentage) \
                .time(timestamp)
                
            bitrate_point = Point("network_metrics") \
                .tag("ue", ue) \
                .field("bitrate", bitrate) \
                .time(timestamp)
            
            # Write to InfluxDB
            self.write_api.write(bucket=self.bucket, record=[loss_point, bitrate_point])
            logger.debug(f"Written metrics for {ue}: loss={loss_percentage}%, bitrate={bitrate}MB")
            return True
            
        except Exception as e:
            logger.error(f"Failed to write metrics for {ue}: {e}")
            return False
    
    def write_dataframe(self, df, ue_column="ue", loss_column="loss_percentage", 
                       bitrate_column="bitrate", timestamp_column="timestamp"):
        """
        Write pandas DataFrame to InfluxDB
        
        Args:
            df: Pandas DataFrame with metrics data
            ue_column (str): Column name for UE identifier
            loss_column (str): Column name for loss percentage
            bitrate_column (str): Column name for bitrate
            timestamp_column (str): Column name for timestamp
        """
        if not self.write_api:
            logger.error("InfluxDB client not connected")
            return False
            
        try:
            points = []
            for _, row in df.iterrows():
                ue = row[ue_column]
                loss = row[loss_column]
                bitrate = row[bitrate_column]
                timestamp = row[timestamp_column]
                
                # Create data points
                loss_point = Point("network_metrics") \
                    .tag("ue", ue) \
                    .field("loss_percentage", loss) \
                    .time(timestamp)
                    
                bitrate_point = Point("network_metrics") \
                    .tag("ue", ue) \
                    .field("bitrate", bitrate) \
                    .time(timestamp)
                
                points.extend([loss_point, bitrate_point])
            
            # Write all points
            self.write_api.write(bucket=self.bucket, record=points)
            logger.info(f"Written {len(points)} data points to InfluxDB")
            return True
            
        except Exception as e:
            logger.error(f"Failed to write DataFrame to InfluxDB: {e}")
            return False
    
    def close(self):
        """Close InfluxDB connection"""
        if self.client:
            self.client.close()
            logger.info("InfluxDB connection closed")
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close() 