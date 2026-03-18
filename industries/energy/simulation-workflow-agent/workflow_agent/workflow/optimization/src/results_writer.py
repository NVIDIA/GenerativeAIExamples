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
Comprehensive results writer for optimization

Saves results in multiple formats:
- JSON: Configuration and summary
- CSV: Detailed evaluation table
- TXT: Human-readable summary
"""

import json
import csv
from pathlib import Path
from datetime import datetime
import numpy as np


class OptimizationResultsWriter:
    """
    Handles comprehensive saving of optimization results
    
    Saves:
    - Configuration parameters as JSON
    - All individual evaluations as CSV
    - Summary as JSON and TXT
    """
    
    def __init__(self, output_dir, run_name=None):
        """
        Initialize results writer
        
        Parameters:
        -----------
        output_dir : str or Path
            Directory to save results
        run_name : str, optional
            Name for this optimization run (default: timestamp)
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        if run_name is None:
            run_name = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.run_name = run_name
        
        # File paths
        self.config_file = self.output_dir / f"{run_name}_config.json"
        self.results_file = self.output_dir / f"{run_name}_results.json"
        self.evaluations_file = self.output_dir / f"{run_name}_evaluations.csv"
        self.summary_file = self.output_dir / f"{run_name}_summary.txt"
        
        # Storage for evaluations
        self.evaluations = []
        self.config_data = {}
        
    def save_configuration(self, config_dict):
        """
        Save optimization configuration to JSON
        
        Parameters:
        -----------
        config_dict : dict
            Configuration parameters
        """
        self.config_data = config_dict.copy()
        
        # Convert Path objects to strings for JSON serialization
        config_serializable = self._make_serializable(config_dict)
        
        # Add metadata
        config_serializable['_metadata'] = {
            'run_name': self.run_name,
            'timestamp': datetime.now().isoformat(),
            'output_directory': str(self.output_dir)
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(config_serializable, f, indent=2)
        
        print(f"Configuration saved to: {self.config_file}")
    
    def add_evaluation(self, generation, individual, case_name, variables, objective, success=True):
        """
        Add an individual evaluation to the results
        
        Parameters:
        -----------
        generation : int
            Generation number
        individual : int
            Individual ID within generation
        case_name : str
            Simulation case name (e.g., SPE10_0_1.DATA)
        variables : dict
            Dictionary of variable names and values
        objective : float
            Objective function value
        success : bool
            Whether simulation succeeded
        """
        evaluation = {
            'generation': generation,
            'individual': individual,
            'case_name': case_name,
            'success': success,
            'objective': objective,
            **variables  # Unpack variable dict
        }
        
        self.evaluations.append(evaluation)
    
    def save_evaluations_table(self):
        """
        Save all evaluations to CSV file
        """
        if not self.evaluations:
            print("Warning: No evaluations to save")
            return
        
        # Get all column names (keys from first evaluation)
        fieldnames = list(self.evaluations[0].keys())
        
        # Write CSV
        with open(self.evaluations_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.evaluations)
        
        print(f"Evaluations table saved to: {self.evaluations_file}")
        return str(self.evaluations_file)
    
    def save_final_results(self, best_individual, algorithm_result=None):
        """
        Save final optimization results
        
        Parameters:
        -----------
        best_individual : dict
            Best individual found (generation, individual, variables, objective)
        algorithm_result : pymoo Result object, optional
            Full pymoo result object
        """
        # Calculate statistics from evaluations
        objectives = [e['objective'] for e in self.evaluations if e.get('success', False)]
        
        # Handle empty evaluations list
        if not objectives:
            print("Warning: No successful evaluations found for statistics")
            objectives = [0.0]
        
        results = {
            'run_info': {
                'run_name': self.run_name,
                'timestamp': datetime.now().isoformat(),
                'output_directory': str(self.output_dir)
            },
            'configuration': {
                'config_file': str(self.config_file),
                **self._make_serializable(self.config_data)
            },
            'evaluations': {
                'total_evaluations': len(self.evaluations),
                'successful_evaluations': sum(1 for e in self.evaluations if e['success']),
                'failed_evaluations': sum(1 for e in self.evaluations if not e['success']),
                'evaluations_table': str(self.evaluations_file)
            },
            'best_solution': best_individual,
            'statistics': {
                'best_objective': float(np.max(objectives)) if objectives else None,
                'worst_objective': float(np.min(objectives)) if objectives else None,
                'mean_objective': float(np.mean(objectives)) if objectives else None,
                'std_objective': float(np.std(objectives)) if objectives else None,
                'median_objective': float(np.median(objectives)) if objectives else None
            }
        }
        
        # Add convergence history (best per generation)
        generations = sorted(set(e['generation'] for e in self.evaluations))
        convergence = []
        for gen in generations:
            gen_evals = [e for e in self.evaluations if e['generation'] == gen and e['success']]
            if gen_evals:
                best_obj = max(e['objective'] for e in gen_evals)
                mean_obj = np.mean([e['objective'] for e in gen_evals])
                worst_obj = min(e['objective'] for e in gen_evals)
                convergence.append({
                    'generation': gen,
                    'best': float(best_obj),
                    'mean': float(mean_obj),
                    'worst': float(worst_obj),
                    'n_evaluations': len(gen_evals)
                })
        results['convergence_history'] = convergence
        
        # Save JSON (ensure numpy types are serialized)
        results_serializable = self._make_serializable(results)
        with open(self.results_file, 'w') as f:
            json.dump(results_serializable, f, indent=2)
        
        print(f"Results JSON saved to: {self.results_file}")
        
        # Save human-readable summary
        self._save_text_summary(results)
        
        return results
    
    def _save_text_summary(self, results):
        """Save human-readable text summary"""
        with open(self.summary_file, 'w') as f:
            f.write("="*60 + "\n")
            f.write("OPTIMIZATION RESULTS SUMMARY\n")
            f.write("="*60 + "\n\n")
            
            f.write(f"Run Name: {results['run_info']['run_name']}\n")
            f.write(f"Timestamp: {results['run_info']['timestamp']}\n")
            f.write(f"Output Directory: {results['run_info']['output_directory']}\n\n")
            
            f.write("-"*60 + "\n")
            f.write("FILES GENERATED\n")
            f.write("-"*60 + "\n")
            f.write(f"Configuration JSON: {self.config_file.name}\n")
            f.write(f"Results JSON: {self.results_file.name}\n")
            f.write(f"Evaluations CSV: {self.evaluations_file.name}\n")
            f.write(f"Summary TXT: {self.summary_file.name}\n\n")
            
            f.write("-"*60 + "\n")
            f.write("OPTIMIZATION CONFIGURATION\n")
            f.write("-"*60 + "\n")
            config = results['configuration']
            if 'pop_size' in config:
                f.write(f"Population size: {config['pop_size']}\n")
            if 'n_generations' in config:
                f.write(f"Generations: {config['n_generations']}\n")
            if 'n_parallel' in config:
                f.write(f"Parallel simulations: {config['n_parallel']}\n")
            if 'objective_mode' in config:
                f.write(f"Objective: {config['objective_mode']}\n")
            if 'variables_config' in config:
                f.write(f"Variables: {list(config['variables_config'].keys())}\n")
            f.write("\n")
            
            f.write("-"*60 + "\n")
            f.write("EVALUATION STATISTICS\n")
            f.write("-"*60 + "\n")
            evals = results['evaluations']
            f.write(f"Total evaluations: {evals['total_evaluations']}\n")
            f.write(f"Successful: {evals['successful_evaluations']}\n")
            f.write(f"Failed: {evals['failed_evaluations']}\n\n")
            
            f.write("-"*60 + "\n")
            f.write("BEST SOLUTION\n")
            f.write("-"*60 + "\n")
            best = results['best_solution']
            f.write(f"Found in generation: {best.get('generation', 'N/A')}\n")
            f.write(f"Individual: {best.get('individual', 'N/A')}\n")
            f.write(f"Case name: {best.get('case_name', 'N/A')}\n")
            f.write(f"Objective value: {best.get('objective', 'N/A'):.4f}\n")
            f.write(f"Variables:\n")
            for var_name, var_value in best.get('variables', {}).items():
                f.write(f"  {var_name}: {var_value}\n")
            f.write("\n")
            
            f.write("-"*60 + "\n")
            f.write("OBJECTIVE STATISTICS\n")
            f.write("-"*60 + "\n")
            stats = results['statistics']
            f.write(f"Best: {stats['best_objective']:.4f}\n")
            f.write(f"Mean: {stats['mean_objective']:.4f}\n")
            f.write(f"Median: {stats['median_objective']:.4f}\n")
            f.write(f"Worst: {stats['worst_objective']:.4f}\n")
            f.write(f"Std Dev: {stats['std_objective']:.4f}\n\n")
            
            f.write("-"*60 + "\n")
            f.write("CONVERGENCE HISTORY\n")
            f.write("-"*60 + "\n")
            f.write(f"{'Gen':<6} {'Best':<12} {'Mean':<12} {'Worst':<12} {'N_Eval':<8}\n")
            f.write("-"*60 + "\n")
            for conv in results['convergence_history']:
                f.write(f"{conv['generation']:<6} {conv['best']:<12.4f} "
                       f"{conv['mean']:<12.4f} {conv['worst']:<12.4f} "
                       f"{conv['n_evaluations']:<8}\n")
            f.write("\n")
            
            f.write("="*60 + "\n")
            f.write("For detailed results, see:\n")
            f.write(f"  - {self.results_file.name} (JSON with full details)\n")
            f.write(f"  - {self.evaluations_file.name} (CSV table of all evaluations)\n")
            f.write("="*60 + "\n")
        
        print(f"Summary text saved to: {self.summary_file}")
    
    def _make_serializable(self, obj):
        """
        Convert objects to JSON-serializable format
        
        Parameters:
        -----------
        obj : any
            Object to convert
            
        Returns:
        --------
        Serializable version of object
        """
        if isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._make_serializable(v) for v in obj]
        elif isinstance(obj, Path):
            return str(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (np.integer, np.floating)):
            return float(obj)
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif hasattr(obj, '__dict__'):
            return {k: self._make_serializable(v) for k, v in obj.__dict__.items() 
                   if not k.startswith('_')}
        else:
            return obj


def create_results_writer(output_dir, run_name=None):
    """
    Factory function to create results writer
    
    Parameters:
    -----------
    output_dir : str or Path
        Output directory
    run_name : str, optional
        Run name (default: timestamp)
        
    Returns:
    --------
    OptimizationResultsWriter
    """
    return OptimizationResultsWriter(output_dir, run_name)

