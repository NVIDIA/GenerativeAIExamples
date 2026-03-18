# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

import os
import sys
import subprocess
import numpy as np
from pathlib import Path

# Add parent directory to path to import sim_utils
sys.path.insert(0, str(Path(__file__).parent.parent))
from sim_utils import EclReader

def calculate_objective(simulation_file_path, mode="EUR", economics=None):
    """
    Read simulation output (time series) and compute objective function
    
    Parameters:
    -----------
    simulation_file_path : str
        Path to simulation .DATA file
    mode : str
        "EUR" for Expected Ultimate Recovery or "NPV" for Net Present Value
    economics : dict, optional
        Economic parameters for NPV calculation:
        - oil_price: $/stb - Oil revenue
        - water_injection_cost: $/stb (negative = cost)
        - water_production_cost: $/stb (negative = cost)
        - discount_rate: annual rate (e.g., 0.1 = 10%)
        - num_wells: number of wells
        - well_length: well length in meters
        - drilling_cost_per_meter: $/m
    
    Returns:
    --------
    float : EUR in Mstb or NPV in $
    """

    reader = EclReader(simulation_file_path)

    # Read time series data: oil production, water production, water injection rates
    time_series = reader.read_smry(keys=["FOPR", "FOPT", "FWPR", "FWIR"])

    field_oil_production_rate = time_series["FIELD"]["FOPR"]  # stb/day
    field_oil_production_total = time_series["FIELD"]["FOPT"]  # stb
    field_water_production_rate = time_series["FIELD"]["FWPR"]  # stb/day
    field_water_injection_rate = time_series["FIELD"]["FWIR"]  # stb/day

    if mode=="EUR":
        eur = field_oil_production_total[-1]/1000
        print(f"Total oil produced: {eur:.2f} Mstb")
        return eur

    time_arr = time_series["TIME"]  # days
    delta_time_arr = np.diff(time_arr)  # time step sizes in days

    # Economic parameters (use provided or defaults)
    if economics is None:
        economics = {
            'oil_price': 60.0,
            'water_injection_cost': -5.0,
            'water_production_cost': -2.0,
            'discount_rate': 0.1,
            'num_wells': 30,
            'well_length': 1700.0,
            'drilling_cost_per_meter': 5000
        }
    
    oil_price = economics['oil_price']
    injection_water_cost = economics['water_injection_cost']
    produced_water_cost = economics['water_production_cost']
    discount_rate = economics['discount_rate']
    
    # Drilling and completion cost
    num_wells = economics['num_wells']
    well_length = economics['well_length']
    drilling_cost_per_meter = economics['drilling_cost_per_meter']
    drilling_cost = num_wells * well_length * drilling_cost_per_meter

    # Calculate production/injection volumes for each time period
    # Skip first time point since we use differences
    oil_volume = field_oil_production_rate[1:] * delta_time_arr  # stb
    water_production_volume = field_water_production_rate[1:] * delta_time_arr  # stb
    water_injection_volume = field_water_injection_rate[1:] * delta_time_arr  # stb

    # Calculate revenue and costs for each time period
    oil_revenue = oil_volume * oil_price
    water_production_costs = water_production_volume * produced_water_cost
    water_injection_costs = water_injection_volume * injection_water_cost

    # Net cash flow for each time period (excluding drilling cost)
    net_cash_flow = oil_revenue + water_production_costs + water_injection_costs

    # Convert time from days to years for discounting
    time_years = time_arr[1:] / 365.25

    # Apply discount factor: (1 + d)^(-t)
    discount_factors = (1 + discount_rate) ** (-time_years)
    discounted_cash_flow = net_cash_flow * discount_factors

    # Calculate NPV: sum of discounted cash flows minus initial drilling cost
    npv = np.sum(discounted_cash_flow) - drilling_cost

    # Simple output: NPV in millions of dollars
    npv_mm = npv / 1e6
    # print(f"NPV = ${npv_mm:.2f} MM")

    return npv
