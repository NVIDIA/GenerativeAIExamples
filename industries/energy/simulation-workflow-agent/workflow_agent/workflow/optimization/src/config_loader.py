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

"""
Configuration loader for optimization parameters

Reads YAML configuration files and provides structured access to parameters
"""

import yaml
from pathlib import Path
from typing import Dict, Any


class OptimizationConfig:
    """
    Configuration class for reservoir optimization
    
    Loads and validates configuration from YAML files
    """
    
    def __init__(self, config_file: str):
        """
        Initialize configuration from YAML file
        
        Parameters:
        -----------
        config_file : str
            Path to YAML configuration file
        """
        self.config_file = Path(config_file)
        
        if not self.config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file}")
        
        # Load YAML
        with open(self.config_file, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Validate and parse
        self._validate_config()
        self._parse_config()
    
    def _validate_config(self):
        """Validate that required sections exist"""
        required_sections = ['paths', 'variables', 'objective']
        
        for section in required_sections:
            if section not in self.config:
                raise ValueError(f"Missing required section '{section}' in config file")
        
        # Check for either 'algorithm' (new format) or 'ga_settings' (legacy format)
        if 'algorithm' not in self.config and 'ga_settings' not in self.config:
            raise ValueError("Missing required section 'algorithm' or 'ga_settings' in config file")
    
    def _parse_config(self):
        """Parse configuration sections into accessible attributes"""
        # Paths
        paths = self.config['paths']
        self.template_path = paths.get('template')
        
        # Handle both old format (sim_dir) and new format (sim_dir_base + case_name)
        if 'sim_dir' in paths:
            # Legacy format: use sim_dir directly
            self.sim_dir = paths['sim_dir']
            self.sim_dir_base = None
            self.case_name = None
        else:
            # New format: construct from base and case name
            self.sim_dir_base = paths.get('sim_dir_base')
            self.case_name = (
                paths.get('case_name')
                or paths.get('sim_dir_name')  # legacy alias
                or paths.get('sim_name')      # older legacy name
                or 'workflow_case'
            )
            # sim_dir will be constructed in run_optimization
            self.sim_dir = None
        
        
        # Variables - convert to optimize_ga.py format
        self.variables_config = {}
        for var_name, var_spec in self.config['variables'].items():
            self.variables_config[var_name] = {
                'min': var_spec['min'],
                'max': var_spec['max'],
                'type': var_spec.get('type', 'int')
            }
        
        # Algorithm settings (support both old and new format)
        if 'algorithm' in self.config:
            # New format with algorithm selection
            algo = self.config['algorithm']
            self.algorithm = algo.get('type', 'GA').upper()
            self.pop_size = algo.get('pop_size', 20)
            self.n_generations = algo.get('n_generations', 10)
            self.n_parallel = algo.get('n_parallel', 4)
            self.seed = algo.get('seed', 42)
            
            # Get algorithm-specific parameters
            if self.algorithm == 'PSO':
                pso_params = algo.get('pso_params', {})
                self.algorithm_params = {
                    'w': pso_params.get('w', 0.9),
                    'c1': pso_params.get('c1', 2.0),
                    'c2': pso_params.get('c2', 2.0),
                    'adaptive': pso_params.get('adaptive', True)
                }
            else:  # GA
                ga_params = algo.get('ga_params', {})
                self.algorithm_params = {
                    'crossover_prob': ga_params.get('crossover_prob', 0.9),
                    'crossover_eta': ga_params.get('crossover_eta', 15),
                    'mutation_prob': ga_params.get('mutation_prob', 0.1),
                    'mutation_eta': ga_params.get('mutation_eta', 20)
                }
        else:
            # Legacy format (ga_settings) - backwards compatibility
            ga = self.config.get('ga_settings', {})
            self.algorithm = 'GA'
            self.pop_size = ga.get('pop_size', 20)
            self.n_generations = ga.get('n_generations', 10)
            self.n_parallel = ga.get('n_parallel', 4)
            self.seed = ga.get('seed', 42)
            self.algorithm_params = {
                'crossover_prob': ga.get('crossover_prob', 0.9),
                'crossover_eta': ga.get('crossover_eta', 15),
                'mutation_prob': ga.get('mutation_prob', 0.1),
                'mutation_eta': ga.get('mutation_eta', 20)
            }
        
        # Objective
        self.objective_mode = self.config['objective'].get('mode', 'EUR')
        
        # Economics settings (for NPV calculation)
        if self.objective_mode == 'NPV':
            # Economics section is required for NPV mode
            if 'economics' not in self.config:
                raise ValueError("Economics section is required when objective mode is 'NPV'")
            
            econ = self.config['economics']
            required_econ_params = ['oil_price', 'num_wells', 'well_length', 'drilling_cost_per_meter']
            missing_params = [p for p in required_econ_params if p not in econ]
            if missing_params:
                raise ValueError(f"Required economics parameters missing: {', '.join(missing_params)}")
            
            self.economics = {
                'oil_price': econ['oil_price'],
                'water_injection_cost': econ.get('water_injection_cost', -5.0),
                'water_production_cost': econ.get('water_production_cost', -2.0),
                'discount_rate': econ.get('discount_rate', 0.1),
                'num_wells': econ['num_wells'],
                'well_length': econ['well_length'],
                'drilling_cost_per_meter': econ['drilling_cost_per_meter']
            }
        else:
            # For EUR mode, use defaults (won't be used anyway)
            self.economics = {
                'oil_price': 60.0,
                'water_injection_cost': -5.0,
                'water_production_cost': -2.0,
                'discount_rate': 0.1,
                'num_wells': 30,
                'well_length': 1700.0,
                'drilling_cost_per_meter': 1000
            }
        
        # Simulation settings
        sim = self.config.get('simulation', {})
        self.timeout = sim.get('timeout', 600)

        self.simulator_command = sim.get('simulator_command')
        if not self.simulator_command:
            raise ValueError("Simulation requires 'simulation.simulator_command'")
        
        # Warm-start settings (for Phase 3 optimization)
        self.initial_population_file = self.config.get('initial_population_file', None)
        self.warm_start_fraction = self.config.get('warm_start_fraction', 0.4)
        
        # Output settings
        output = self.config.get('output', {})
        self.run_name = output.get('run_name', None)
        self.save_comprehensive = output.get('save_comprehensive', True)
        self.save_log = output.get('save_log', False)
        default_log_name = f"{self.case_name}.log" if self.case_name else "optimization.log"
        self.log_file = output.get('log_file', default_log_name)
        self.save_plots = output.get('save_plots', False)
        self.plots_dir = output.get('plots_dir', 'plots')
    
    def print_summary(self):
        """Print configuration summary"""
        print("="*60)
        print(f"CONFIGURATION: {self.config_file.name}")
        print("="*60)
        print("\nPaths:")
        print(f"  Template: {self.template_path}")
        if self.sim_dir:
            print(f"  Simulation directory: {self.sim_dir}")
        else:
            print(f"  Simulation base: {self.sim_dir_base}")
            print(f"  Case name: {self.case_name}")
            print(f"  (Final sim_dir: {self.case_name}.sim)")
        print(f"  Simulator command: {self.simulator_command}")
        
        print("\nOptimization Variables:")
        for var_name, var_spec in self.config['variables'].items():
            print(f"  {var_name}: [{var_spec['min']}, {var_spec['max']}]")
            if 'description' in var_spec:
                print(f"    {var_spec['description']}")
        
        print(f"\nOptimization Algorithm: {self.algorithm}")
        print(f"  Population size: {self.pop_size}")
        print(f"  Generations/Iterations: {self.n_generations}")
        print(f"  Parallel simulations: {self.n_parallel}")
        print(f"  Total evaluations: {self.pop_size * self.n_generations}")
        
        if self.algorithm == 'PSO':
            print(f"\nPSO Parameters:")
            print(f"  Inertia weight (w): {self.algorithm_params.get('w')}")
            print(f"  Cognitive (c1): {self.algorithm_params.get('c1')}")
            print(f"  Social (c2): {self.algorithm_params.get('c2')}")
            print(f"  Adaptive: {self.algorithm_params.get('adaptive')}")
        else:  # GA
            print(f"\nGA Parameters:")
            print(f"  Crossover prob: {self.algorithm_params.get('crossover_prob')}")
            print(f"  Crossover eta: {self.algorithm_params.get('crossover_eta')}")
            print(f"  Mutation prob: {self.algorithm_params.get('mutation_prob')}")
            print(f"  Mutation eta: {self.algorithm_params.get('mutation_eta')}")
        
        print("\nObjective:")
        print(f"  Mode: {self.objective_mode}")
        
        if self.objective_mode == "NPV":
            print("\nEconomics:")
            print(f"  Oil price: ${self.economics['oil_price']:.2f}/stb")
            print(f"  Water injection cost: ${self.economics['water_injection_cost']:.2f}/stb")
            print(f"  Water production cost: ${self.economics['water_production_cost']:.2f}/stb")
            print(f"  Discount rate: {self.economics['discount_rate']*100:.1f}%")
            print(f"  Number of wells: {self.economics['num_wells']}")
            print(f"  Well length: {self.economics['well_length']:.1f} m")
            print(f"  Drilling cost: ${self.economics['drilling_cost_per_meter']:.0f}/m")
        
        print("\nSimulation:")
        print(f"  Timeout: {self.timeout}s")
        
        print("\nOutput:")
        print(f"  Run name: {self.run_name if self.run_name else 'auto-generated'}")
        print(f"  Save comprehensive results: {self.save_comprehensive}")
        print(f"  Save log: {self.save_log}")
        if self.save_log:
            print(f"  Log file: {self.log_file}")
        print(f"  Save plots: {self.save_plots}")
        if self.save_plots:
            print(f"  Plots directory: {self.plots_dir}")
        print("="*60 + "\n")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary for function arguments
        
        Returns:
        --------
        dict : Configuration parameters as dictionary
        """
        result = {
            'template_path': self.template_path,
            'variables_config': self.variables_config,
            'pop_size': self.pop_size,
            'n_generations': self.n_generations,
            'objective_mode': self.objective_mode,
            'economics': self.economics,
            'n_parallel': self.n_parallel,
            'simulator_command': self.simulator_command,
            'run_name': self.run_name,
            'save_comprehensive': self.save_comprehensive,
            'algorithm': self.algorithm,
            'algorithm_params': self.algorithm_params,
            'initial_population_file': self.initial_population_file,
            'warm_start_fraction': self.warm_start_fraction
        }
        
        # Add sim_dir or sim_dir_base/case_name depending on format
        if self.sim_dir:
            result['sim_dir'] = self.sim_dir
        else:
            result['sim_dir_base'] = self.sim_dir_base
            result['case_name'] = self.case_name
        
        return result


def load_config(config_file: str) -> OptimizationConfig:
    """
    Load optimization configuration from YAML file
    
    Parameters:
    -----------
    config_file : str
        Path to YAML configuration file
        
    Returns:
    --------
    OptimizationConfig : Parsed configuration object
    """
    return OptimizationConfig(config_file)

