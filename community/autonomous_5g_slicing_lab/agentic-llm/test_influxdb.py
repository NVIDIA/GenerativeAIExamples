#!/usr/bin/env python3
"""
Test script for InfluxDB connection and data writing
"""
import time
from datetime import datetime, timedelta
import random
from influxdb_utils import InfluxDBMetricsClient

def test_influxdb_connection():
    """Test InfluxDB connection and data writing"""
    print("🔍 Testing InfluxDB connection...")
    
    # Initialize client
    client = InfluxDBMetricsClient(url="http://localhost:9001")
    
    # Test connection
    if not client.connect():
        print("❌ Failed to connect to InfluxDB")
        print("💡 Make sure InfluxDB is running: docker-compose up -d")
        return False
    
    print("✅ Successfully connected to InfluxDB")
    
    # Generate test data
    print("📊 Writing test data...")
    
    # Write some test metrics for the last 5 minutes
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(minutes=5)
    
    current_time = start_time
    while current_time <= end_time:
        # Generate realistic test data
        ue1_loss = random.uniform(0, 5)  # 0-5% packet loss
        ue1_bitrate = random.uniform(30, 60)  # 30-60 MB/s
        
        ue2_loss = random.uniform(0, 8)  # 0-8% packet loss
        ue2_bitrate = random.uniform(25, 55)  # 25-55 MB/s
        
        # Write UE1 data
        client.write_metrics(
            ue="UE1",
            loss_percentage=ue1_loss,
            bitrate=ue1_bitrate,
            timestamp=current_time
        )
        
        # Write UE2 data
        client.write_metrics(
            ue="UE2",
            loss_percentage=ue2_loss,
            bitrate=ue2_bitrate,
            timestamp=current_time
        )
        
        current_time += timedelta(seconds=10)  # Data point every 10 seconds
    
    print("✅ Test data written successfully!")
    print(f"📈 Generated {60} data points (30 per UE) over 5 minutes")
    
    # Close connection
    client.close()
    print("🔌 InfluxDB connection closed")
    
    print("\n🎉 Test completed successfully!")
    print("📊 You can now view the data in Grafana at: http://localhost:9002")
    print("   Username: admin, Password: admin")
    
    return True

if __name__ == "__main__":
    test_influxdb_connection() 