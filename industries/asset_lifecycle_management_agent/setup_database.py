#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2023-2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
NASA Turbofan Engine Dataset to SQLite Database Converter

This script converts the NASA Turbofan Engine Degradation Simulation Dataset (C-MAPSS)
from text files into a structured SQLite database for use with the Asset Lifecycle Management agent.

The NASA dataset contains:
- Training data: Engine run-to-failure trajectories
- Test data: Engine trajectories of unknown remaining cycles
- RUL data: Ground truth remaining useful life values

Dataset structure:
- unit_number: Engine unit identifier
- time_in_cycles: Operational time cycles
- operational_setting_1, 2, 3: Operating conditions
- sensor_measurement_1 to 21: Sensor readings
"""

import sqlite3
import pandas as pd
import numpy as np
import os
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NASADatasetProcessor:
    """Processes NASA Turbofan Engine Dataset and creates SQLite database."""
    
    def __init__(self, data_dir: str = "data", db_path: str = "database/nasa_turbo.db"):
        """
        Initialize the processor.
        
        Args:
            data_dir: Directory containing NASA dataset text files
            db_path: Path where SQLite database will be created
        """
        self.data_dir = Path(data_dir)
        self.db_path = Path(db_path)
        
        # Ensure database directory exists
        self.db_path.parent.mkdir(exist_ok=True)
        
        # Define column names for the dataset
        self.columns = [
            'unit_number', 'time_in_cycles',
            'operational_setting_1', 'operational_setting_2', 'operational_setting_3',
            'sensor_measurement_1', 'sensor_measurement_2', 'sensor_measurement_3',
            'sensor_measurement_4', 'sensor_measurement_5', 'sensor_measurement_6',
            'sensor_measurement_7', 'sensor_measurement_8', 'sensor_measurement_9',
            'sensor_measurement_10', 'sensor_measurement_11', 'sensor_measurement_12',
            'sensor_measurement_13', 'sensor_measurement_14', 'sensor_measurement_15',
            'sensor_measurement_16', 'sensor_measurement_17', 'sensor_measurement_18',
            'sensor_measurement_19', 'sensor_measurement_20', 'sensor_measurement_21'
        ]
        
        # Sensor descriptions for metadata
        self.sensor_descriptions = {
            'sensor_measurement_1': 'Total temperature at fan inlet (°R)',
            'sensor_measurement_2': 'Total temperature at LPC outlet (°R)',
            'sensor_measurement_3': 'Total temperature at HPC outlet (°R)',
            'sensor_measurement_4': 'Total temperature at LPT outlet (°R)',
            'sensor_measurement_5': 'Pressure at fan inlet (psia)',
            'sensor_measurement_6': 'Total pressure in bypass-duct (psia)',
            'sensor_measurement_7': 'Total pressure at HPC outlet (psia)',
            'sensor_measurement_8': 'Physical fan speed (rpm)',
            'sensor_measurement_9': 'Physical core speed (rpm)',
            'sensor_measurement_10': 'Engine pressure ratio (P50/P2)',
            'sensor_measurement_11': 'Static pressure at HPC outlet (psia)',
            'sensor_measurement_12': 'Ratio of fuel flow to Ps30 (pps/psi)',
            'sensor_measurement_13': 'Corrected fan speed (rpm)',
            'sensor_measurement_14': 'Corrected core speed (rpm)',
            'sensor_measurement_15': 'Bypass Ratio',
            'sensor_measurement_16': 'Burner fuel-air ratio',
            'sensor_measurement_17': 'Bleed Enthalpy',
            'sensor_measurement_18': 'Required fan speed',
            'sensor_measurement_19': 'Required fan conversion speed',
            'sensor_measurement_20': 'High-pressure turbines Cool air flow',
            'sensor_measurement_21': 'Low-pressure turbines Cool air flow'
        }

    def read_data_file(self, file_path: Path) -> pd.DataFrame:
        """
        Read a NASA dataset text file and return as DataFrame.
        
        Args:
            file_path: Path to the text file
            
        Returns:
            DataFrame with proper column names
        """
        try:
            # Read space-separated text file
            df = pd.read_csv(file_path, sep='\s+', header=None, names=self.columns)
            logger.info(f"Loaded {len(df)} records from {file_path.name}")
            return df
        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")
            return pd.DataFrame()

    def process_training_data(self, conn: sqlite3.Connection):
        """Process training data files and create database tables."""
        logger.info("Processing training data...")
        
        training_files = [
            'train_FD001.txt', 'train_FD002.txt', 'train_FD003.txt', 'train_FD004.txt'
        ]
        
        for file_name in training_files:
            file_path = self.data_dir / file_name
            if file_path.exists():
                df = self.read_data_file(file_path)
                if not df.empty:
                    # Calculate RUL for training data (max cycle - current cycle)
                    df['RUL'] = df.groupby('unit_number')['time_in_cycles'].transform('max') - df['time_in_cycles']
                    
                    # Create separate table for each dataset (e.g., train_FD001)
                    table_name = file_name.replace('.txt', '')
                    df.to_sql(table_name, conn, if_exists='replace', index=False)
                    logger.info(f"Created {table_name} table with {len(df)} records")
            else:
                logger.warning(f"Training file not found: {file_path}")

    def process_test_data(self, conn: sqlite3.Connection):
        """Process test data files and create database tables."""
        logger.info("Processing test data...")
        
        test_files = [
            'test_FD001.txt', 'test_FD002.txt', 'test_FD003.txt', 'test_FD004.txt'
        ]
        
        for file_name in test_files:
            file_path = self.data_dir / file_name
            if file_path.exists():
                df = self.read_data_file(file_path)
                if not df.empty:
                    # Create separate table for each dataset (e.g., test_FD001)
                    table_name = file_name.replace('.txt', '')
                    df.to_sql(table_name, conn, if_exists='replace', index=False)
                    logger.info(f"Created {table_name} table with {len(df)} records")
            else:
                logger.warning(f"Test file not found: {file_path}")

    def process_rul_data(self, conn: sqlite3.Connection):
        """Process RUL (Remaining Useful Life) data files."""
        logger.info("Processing RUL data...")
        
        rul_files = [
            'RUL_FD001.txt', 'RUL_FD002.txt', 'RUL_FD003.txt', 'RUL_FD004.txt'
        ]
        
        for file_name in rul_files:
            file_path = self.data_dir / file_name
            if file_path.exists():
                try:
                    # RUL files contain one RUL value per line for each test engine
                    rul_values = pd.read_csv(file_path, header=None, names=['RUL'])
                    rul_values['unit_number'] = range(1, len(rul_values) + 1)
                    
                    # Create separate table for each dataset (e.g., RUL_FD001)
                    table_name = file_name.replace('.txt', '')
                    rul_values[['unit_number', 'RUL']].to_sql(table_name, conn, if_exists='replace', index=False)
                    logger.info(f"Created {table_name} table with {len(rul_values)} records")
                except Exception as e:
                    logger.error(f"Error reading RUL file {file_path}: {e}")
            else:
                logger.warning(f"RUL file not found: {file_path}")

    def create_metadata_tables(self, conn: sqlite3.Connection):
        """Create metadata tables with sensor descriptions and dataset information."""
        logger.info("Creating metadata tables...")
        
        # Sensor metadata
        sensor_metadata = pd.DataFrame([
            {'sensor_name': sensor, 'description': desc}
            for sensor, desc in self.sensor_descriptions.items()
        ])
        sensor_metadata.to_sql('sensor_metadata', conn, if_exists='replace', index=False)
        
        # Dataset metadata
        dataset_metadata = pd.DataFrame([
            {'dataset': 'FD001', 'description': 'Sea level conditions', 'fault_modes': 1},
            {'dataset': 'FD002', 'description': 'Sea level conditions', 'fault_modes': 6},
            {'dataset': 'FD003', 'description': 'High altitude conditions', 'fault_modes': 1},
            {'dataset': 'FD004', 'description': 'High altitude conditions', 'fault_modes': 6}
        ])
        dataset_metadata.to_sql('dataset_metadata', conn, if_exists='replace', index=False)
        
        logger.info("Created metadata tables")

    def create_indexes(self, conn: sqlite3.Connection):
        """Create database indexes for better query performance."""
        logger.info("Creating database indexes...")
        
        datasets = ['FD001', 'FD002', 'FD003', 'FD004']
        indexes = []
        
        # Create indexes for each dataset's tables
        for dataset in datasets:
            indexes.extend([
                f"CREATE INDEX IF NOT EXISTS idx_train_{dataset}_unit ON train_{dataset}(unit_number)",
                f"CREATE INDEX IF NOT EXISTS idx_train_{dataset}_cycle ON train_{dataset}(time_in_cycles)",
                f"CREATE INDEX IF NOT EXISTS idx_test_{dataset}_unit ON test_{dataset}(unit_number)",
                f"CREATE INDEX IF NOT EXISTS idx_test_{dataset}_cycle ON test_{dataset}(time_in_cycles)",
                f"CREATE INDEX IF NOT EXISTS idx_RUL_{dataset}_unit ON RUL_{dataset}(unit_number)"
            ])
        
        for index_sql in indexes:
            try:
                conn.execute(index_sql)
            except Exception as e:
                logger.warning(f"Failed to create index: {e}")
        
        conn.commit()
        logger.info("Created database indexes")

    def create_views(self, conn: sqlite3.Connection):
        """Create useful database views for common queries."""
        logger.info("Creating database views...")
        
        # View for latest sensor readings per engine
        latest_readings_view = """
        CREATE VIEW IF NOT EXISTS latest_sensor_readings AS
        SELECT t1.*
        FROM training_data t1
        INNER JOIN (
            SELECT unit_number, dataset, MAX(time_in_cycles) as max_cycle
            FROM training_data
            GROUP BY unit_number, dataset
        ) t2 ON t1.unit_number = t2.unit_number 
               AND t1.dataset = t2.dataset 
               AND t1.time_in_cycles = t2.max_cycle
        """
        
        # View for engine health summary
        engine_health_view = """
        CREATE VIEW IF NOT EXISTS engine_health_summary AS
        SELECT 
            unit_number,
            dataset,
            MAX(time_in_cycles) as total_cycles,
            MIN(RUL) as final_rul,
            AVG(sensor_measurement_1) as avg_fan_inlet_temp,
            AVG(sensor_measurement_11) as avg_hpc_outlet_pressure,
            AVG(sensor_measurement_21) as avg_lpt_cool_air_flow
        FROM training_data
        GROUP BY unit_number, dataset
        """
        
        conn.execute(latest_readings_view)
        conn.execute(engine_health_view)
        conn.commit()
        logger.info("Created database views")

    def validate_database(self, conn: sqlite3.Connection):
        """Validate the created database by running sample queries."""
        logger.info("Validating database...")
        
        validation_queries = [
            ("Training data count", "SELECT COUNT(*) FROM training_data"),
            ("Test data count", "SELECT COUNT(*) FROM test_data"),
            ("RUL data count", "SELECT COUNT(*) FROM rul_data"),
            ("Unique engines in training", "SELECT COUNT(DISTINCT unit_number) FROM training_data"),
            ("Datasets available", "SELECT DISTINCT dataset FROM training_data"),
        ]
        
        for description, query in validation_queries:
            try:
                result = conn.execute(query).fetchone()
                logger.info(f"{description}: {result[0] if isinstance(result[0], (int, float)) else result}")
            except Exception as e:
                logger.error(f"Validation query failed - {description}: {e}")

    def process_dataset(self):
        """Main method to process the entire NASA dataset."""
        logger.info(f"Starting NASA dataset processing...")
        logger.info(f"Data directory: {self.data_dir.absolute()}")
        logger.info(f"Database path: {self.db_path.absolute()}")
        
        # Check if data directory exists
        if not self.data_dir.exists():
            logger.error(f"Data directory not found: {self.data_dir}")
            logger.info("Please download the NASA Turbofan Engine Degradation Simulation Dataset")
            logger.info("and place the text files in the 'data' directory")
            return False
        
        try:
            # Connect to SQLite database
            with sqlite3.connect(self.db_path) as conn:
                logger.info(f"Connected to database: {self.db_path}")
                
                # Process all data files
                self.process_training_data(conn)
                self.process_test_data(conn)
                self.process_rul_data(conn)
                self.create_metadata_tables(conn)
                self.create_indexes(conn)
                self.create_views(conn)
                
                # Validate the database
                self.validate_database(conn)
                
                logger.info("Database processing completed successfully!")
                return True
                
        except Exception as e:
            logger.error(f"Error processing database: {e}")
            return False

def main():
    """Main function to run the database setup."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Convert NASA Turbofan Dataset to SQLite")
    parser.add_argument("--data-dir", default="data", 
                       help="Directory containing NASA dataset text files")
    parser.add_argument("--db-path", default="database/nasa_turbo.db",
                       help="Path for output SQLite database")
    
    args = parser.parse_args()
    
    processor = NASADatasetProcessor(args.data_dir, args.db_path)
    success = processor.process_dataset()
    
    if success:
        print(f"\n✅ Database created successfully at: {args.db_path}")
        print("\nDatabase contains the following tables:")
        print("- training_data: Engine run-to-failure trajectories")
        print("- test_data: Engine test trajectories")
        print("- rul_data: Ground truth RUL values")
        print("- sensor_metadata: Sensor descriptions")
        print("- dataset_metadata: Dataset information")
        print("\nUseful views created:")
        print("- latest_sensor_readings: Latest readings per engine")
        print("- engine_health_summary: Engine health statistics")
    else:
        print("\n❌ Database creation failed. Check the logs above.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 