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
Optimization Orchestrator for Reservoir Simulation using pymoo

This module orchestrates the entire optimization workflow:
1. Template substitution - replaces ${variable} placeholders with actual values
2. Simulation execution - generates and runs OPM Flow simulations in parallel
3. Objective evaluation - calculates EUR or NPV from simulation results
4. Algorithm management - configures and runs pymoo optimization algorithms
5. Results collection - aggregates and saves comprehensive results

Supported algorithms:
- GA (Genetic Algorithm): Evolutionary optimization with crossover and mutation
- PSO (Particle Swarm Optimization): Swarm-based optimization

The orchestrator coordinates:
- Problem definition (ReservoirOptimizationProblem class)
- Parallel simulation execution (ProcessPoolExecutor)
- Objective function evaluation (via objectives.py)
- Results writing (via results_writer.py)
"""

import os
import sys
import re
import subprocess
import shlex
import numpy as np
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from string import Template

# Add parent directory to path for sim_utils
sys.path.insert(0, str(Path(__file__).parent.parent))

from pymoo.core.problem import Problem
from pymoo.algorithms.soo.nonconvex.ga import GA
from pymoo.algorithms.soo.nonconvex.pso import PSO
from pymoo.operators.crossover.sbx import SBX
from pymoo.operators.mutation.pm import PM
from pymoo.operators.sampling.rnd import IntegerRandomSampling
from pymoo.optimize import minimize
from pymoo.termination import get_termination

# Import from same directory
from objectives import calculate_objective
from results_writer import OptimizationResultsWriter
from plot_progress import plot_optimization_progress, plot_simple_progress


class ReservoirOptimizationProblem(Problem):
    """
    Pymoo Problem class for reservoir optimization
    
    Optimizes well placement parameters in a reservoir simulation template
    """
    
    def __init__(self, 
                 template_path,
                 sim_dir,
                 variables_config,
                 objective_mode="EUR",
                 economics=None,
                 n_parallel=4,
                 simulator_command=None,
                 results_writer=None,
                 timeout=600):
        """
        Initialize the optimization problem
        
        Parameters:
        -----------
        template_path : str
            Path to template .DATA file with ${variable} placeholders
        sim_dir : str
            Directory where simulation files will be generated
        variables_config : dict
            Dictionary defining optimization variables, e.g.:
            {
                'I2_I': {'min': 1, 'max': 60, 'type': 'int'},
                'I2_J': {'min': 1, 'max': 220, 'type': 'int'}
            }
        objective_mode : str
            'EUR' for cumulative oil production or 'NPV' for net present value
        economics : dict, optional
            Economic parameters for NPV calculation
        n_parallel : int
            Number of parallel simulations to run
        simulator_command : str, optional
            Custom simulator command with ${sim_file_path} placeholder
        results_writer : OptimizationResultsWriter, optional
            Results writer for comprehensive result saving
        timeout : int
            Simulation timeout in seconds (default: 600)
        """
        
        self.template_path = Path(template_path)
        self.sim_dir = Path(sim_dir)
        self.variables_config = variables_config
        self.objective_mode = objective_mode
        self.economics = economics
        self.n_parallel = n_parallel
        self.simulator_command = simulator_command
        self.results_writer = results_writer
        self.timeout = timeout
        
        # Create simulation directory if it doesn't exist
        self.sim_dir.mkdir(parents=True, exist_ok=True)
        
        # Read template file
        with open(self.template_path, 'r') as f:
            self.template_content = f.read()
        
        # Extract variable names and bounds
        var_names = list(variables_config.keys())
        xl = [variables_config[v]['min'] for v in var_names]
        xu = [variables_config[v]['max'] for v in var_names]
        
        # Initialize pymoo Problem (single objective, minimization)
        # We minimize negative EUR/NPV to maximize the actual value
        # Add constraints to prevent well overlaps
        super().__init__(n_var=len(var_names),
                        n_obj=1,
                        n_constr=1,  # One constraint: no well overlaps
                        xl=np.array(xl),
                        xu=np.array(xu),
                        type_var=int)
        
        self.var_names = var_names
        self.generation = 0
        self.eval_counter = 0
        self.best_history = []  # Track best objective per generation
        self.n_generations = None  # Will be set by run_optimization
        
        print(f"Optimization Problem Initialized:")
        print(f"  Template: {self.template_path}")
        print(f"  Simulation directory: {self.sim_dir}")
        print(f"  Variables: {self.var_names}")
        print(f"  Bounds: xl={xl}, xu={xu}")
        print(f"  Objective: Maximize {objective_mode}")
        print(f"  Parallel simulations: {n_parallel}")
        print(f"  Note: INCLUDE files will be shared from {self.template_path.parent.parent / 'INCLUDE'}")
    
    def _check_well_overlaps(self, x):
        """
        Check if any wells overlap at the same (I, J) location
        
        Parameters:
        -----------
        x : array
            Decision variables
            
        Returns:
        --------
        int : Number of overlapping well pairs (0 = no overlaps)
        """
        # Extract I and J coordinates for all wells
        var_dict = {name: int(val) for name, val in zip(self.var_names, x)}
        
        # Build list of (I, J) tuples for each well
        well_locations = []
        well_names = set()
        
        # Extract well names (e.g., "BR_I_1", "BR_P_5")
        for var_name in var_dict.keys():
            # Variable name format: WELLNAME_I or WELLNAME_J
            if var_name.endswith('_I'):
                well_name = var_name[:-2]  # Remove '_I'
                well_names.add(well_name)
        
        # For each well, get its (I, J) location
        for well_name in well_names:
            i_var = f"{well_name}_I"
            j_var = f"{well_name}_J"
            
            if i_var in var_dict and j_var in var_dict:
                location = (var_dict[i_var], var_dict[j_var])
                well_locations.append(location)
        
        # Check for duplicates
        unique_locations = set(well_locations)
        num_overlaps = len(well_locations) - len(unique_locations)
        
        return num_overlaps
    
    def _print_generation_progress(self, current_best):
        """
        Print visual progress summary at end of generation
        
        Parameters:
        -----------
        current_best : float
            Best objective value for current generation
        """
        # Add to history
        self.best_history.append(current_best)
        
        gen = self.generation
        n_gen = self.n_generations if self.n_generations else "?"
        
        # Progress bar
        if self.n_generations:
            progress_pct = (gen + 1) / self.n_generations
            bar_length = 40
            filled = int(bar_length * progress_pct)
            bar = '█' * filled + '░' * (bar_length - filled)
            progress_str = f"[{bar}] {progress_pct*100:.1f}%"
        else:
            progress_str = f"Gen {gen+1}"
        
        # Format objective value
        if self.objective_mode == "NPV":
            obj_str = f"${current_best/1e6:.2f} MM"
        else:
            obj_str = f"{current_best:.2f}"
        
        # Calculate improvement
        if len(self.best_history) > 1:
            prev_best = self.best_history[-2]
            improvement = current_best - prev_best
            if self.objective_mode == "NPV":
                imp_str = f"{improvement/1e6:+.2f} MM"
            else:
                imp_str = f"{improvement:+.2f}"
            imp_pct = (improvement / abs(prev_best)) * 100 if prev_best != 0 else 0
            imp_display = f"({imp_pct:+.2f}%)"
        else:
            imp_str = "---"
            imp_display = ""
        
        # Simple sparkline of recent history (last 10 generations)
        history_window = self.best_history[-10:]
        if len(history_window) > 1:
            min_val = min(history_window)
            max_val = max(history_window)
            range_val = max_val - min_val if max_val > min_val else 1
            
            # Create mini bar chart (scaled 0-8 levels)
            bars = "▁▂▃▄▅▆▇█"
            sparkline = ""
            for val in history_window:
                level = int(((val - min_val) / range_val) * 7) if range_val > 0 else 4
                sparkline += bars[level]
        else:
            sparkline = "▄"
        
        # Print summary
        print(f"\n{'='*70}")
        print(f"  Generation {gen+1}/{n_gen}  {progress_str}")
        print(f"{'='*70}")
        print(f"  Best {self.objective_mode}: {obj_str}  |  Δ: {imp_str} {imp_display}")
        print(f"  Trend (last 10): {sparkline}")
        print(f"{'='*70}\n")
    
    def _substitute_template(self, variables_dict):
        """
        Substitute template variables with actual values
        
        Parameters:
        -----------
        variables_dict : dict
            Dictionary with variable names as keys and values to substitute
            
        Returns:
        --------
        str : Substituted simulation deck content
        """
        content = self.template_content
        for var_name, var_value in variables_dict.items():
            # Replace ${VAR} with actual value
            content = content.replace(f"${{{var_name}}}", str(int(var_value)))
        return content
    
    def _generate_simulation_file(self, x, gen_id, ind_id):
        """
        Generate a simulation .DATA file for a given individual
        
        Parameters:
        -----------
        x : array
            Decision variables
        gen_id : int
            Generation ID
        ind_id : int
            Individual ID within generation
            
        Returns:
        --------
        Path : Path to generated simulation file
        """
        # Create variable dictionary
        var_dict = {name: val for name, val in zip(self.var_names, x)}
        
        # Substitute template
        sim_content = self._substitute_template(var_dict)
        
        # Generate filename
        base_name = self.template_path.stem  # e.g., SPE10
        sim_filename = f"{base_name}_{gen_id}_{ind_id}.DATA"
        sim_filepath = self.sim_dir / sim_filename
        
        # Write simulation file
        with open(sim_filepath, 'w') as f:
            f.write(sim_content)
        
        return sim_filepath
    
    def _run_simulation(self, sim_filepath):
        """
        Run OPM Flow simulation for a given .DATA file
        
        Parameters:
        -----------
        sim_filepath : Path
            Path to simulation .DATA file
            
        Returns:
        --------
        bool : True if simulation completed successfully, False otherwise
        """
        try:
            # Change to simulation directory for execution
            sim_dir = sim_filepath.parent
            sim_filename = sim_filepath.name
            
            sim_path = str(sim_filepath.resolve())
            command = self.simulator_command.replace("${sim_file_path}", sim_path)
            command = command.replace("sim_file_path", sim_path)
            # Inject OPM_FLOW_EXTRA_ARGS (e.g. --CheckSatfuncConsistency=0) before data file
            extra = os.environ.get("OPM_FLOW_EXTRA_ARGS", "")
            if extra:
                command = command.replace(sim_path, extra.strip() + " " + sim_path)
            cmd_list = shlex.split(command)

            # Run OPM Flow
            result = subprocess.run(
                cmd_list,
                cwd=sim_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=self.timeout,
                text=True
            )
            
            if result.returncode == 0:
                return True
            else:
                print(f"  Warning: Simulation {sim_filename} failed with code {result.returncode}")
                if result.stderr:
                    for line in result.stderr.strip().split("\n")[-10:]:  # last 10 lines
                        print(f"    {line}")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"  Warning: Simulation {sim_filepath.name} timed out")
            return False
        except Exception as e:
            print(f"  Error running simulation {sim_filepath.name}: {e}")
            return False
    
    def _evaluate_objective(self, sim_filepath):
        """
        Evaluate objective function from simulation results
        
        Parameters:
        -----------
        sim_filepath : Path
            Path to simulation .DATA file
            
        Returns:
        --------
        float : Objective function value (EUR or NPV)
        """
        try:
            # Use the calculate_objective function from objectives.py
            obj_value = calculate_objective(
                str(sim_filepath), 
                mode=self.objective_mode,
                economics=self.economics
            )
            return obj_value
        except Exception as e:
            print(f"  Error evaluating {sim_filepath.name}: {e}")
            return -1e10  # Return worst case value
    
    def _evaluate_individual(self, x, gen_id, ind_id):
        """
        Evaluate a single individual: generate file, run simulation, calculate objective
        
        Parameters:
        -----------
        x : array
            Decision variables
        gen_id : int
            Generation ID
        ind_id : int
            Individual ID
            
        Returns:
        --------
        tuple : (objective_value, evaluation_dict)
            objective_value: negative objective for minimization
            evaluation_dict: dict with evaluation details for logging
        """
        # Generate simulation file
        sim_filepath = self._generate_simulation_file(x, gen_id, ind_id)
        case_name = sim_filepath.name
        
        # Create variables dictionary
        var_dict = {name: int(val) for name, val in zip(self.var_names, x)}
        
        # Run simulation
        success = self._run_simulation(sim_filepath)
        
        if not success:
            obj_value = 0.0
            eval_dict = {
                'generation': gen_id,
                'individual': ind_id,
                'case_name': case_name,
                'variables': var_dict,
                'objective': obj_value,
                'success': False
            }
            return 1e10, eval_dict  # Large penalty for failed simulations
        
        # Evaluate objective
        obj_value = self._evaluate_objective(sim_filepath)
        
        # Create evaluation dict
        eval_dict = {
            'generation': gen_id,
            'individual': ind_id,
            'case_name': case_name,
            'variables': var_dict,
            'objective': obj_value,
            'success': True
        }
        
        # Return negative value (pymoo minimizes, we want to maximize EUR/NPV)
        return -obj_value, eval_dict
    
    def _evaluate(self, X, out, *args, **kwargs):
        """
        Pymoo's evaluation method - evaluates a population
        
        Parameters:
        -----------
        X : array (n_individuals, n_variables)
            Population to evaluate
        out : dict
            Output dictionary to store objective values
        """
        n_individuals = X.shape[0]
        objectives = np.zeros(n_individuals)
        
        print(f"\n{'='*60}")
        print(f"Generation {self.generation}: Evaluating {n_individuals} individuals")
        print(f"{'='*60}")
        
        # Prepare tasks for parallel execution
        tasks = []
        for i in range(len(X)):
            tasks.append((X[i], self.generation, i))
        simulated_objectives = np.zeros(len(X))
        
        # Run simulations in parallel
        
        with ProcessPoolExecutor(max_workers=self.n_parallel) as executor:
            # Submit all tasks
            futures = {
                executor.submit(self._evaluate_individual, x, gen_id, ind_id): (ind_id, x)
                for x, gen_id, ind_id in tasks
            }
            
            # Collect results as they complete
            for future in as_completed(futures):
                ind_id, x = futures[future]
                try:
                    obj_value, eval_dict = future.result()
                    simulated_objectives[ind_id] = obj_value
                    
                    # Log evaluation to results writer (in main process)
                    if self.results_writer:
                        self.results_writer.add_evaluation(
                            generation=eval_dict['generation'],
                            individual=eval_dict['individual'],
                            case_name=eval_dict['case_name'],
                            variables=eval_dict['variables'],
                            objective=eval_dict['objective'],
                            success=eval_dict['success']
                        )
                    
                    # Simple output: individual number and objective value
                    if self.objective_mode == "NPV":
                        obj_display = f"${-obj_value/1e6:.2f} MM"
                    else:
                        obj_display = f"{-obj_value:.2f}"
                    print(f"  Individual {ind_id}: {self.objective_mode} = {obj_display}")
                    
                except Exception as e:
                    print(f"  Error evaluating individual {ind_id}: {e}")
                    simulated_objectives[ind_id] = 1e10
        
        objectives = simulated_objectives
        
        # Check constraints (well overlaps) for evaluated individuals
        constraints = np.zeros(len(X))
        num_violations = 0
        
        for i in range(len(X)):
            num_overlaps = self._check_well_overlaps(X[i])
            constraints[i] = num_overlaps  # Constraint: must be ≤ 0 (feasible)
            if num_overlaps > 0:
                num_violations += 1
        
        if num_violations > 0:
            print(f"\n  ⚠️  Warning: {num_violations} individuals have overlapping wells")
        
        # Store best individual of this generation
        best_idx = np.argmin(objectives)
        best_obj = -objectives[best_idx]
        best_x = X[best_idx]
        
        # Print visual progress summary
        self._print_generation_progress(best_obj)
        
        out["F"] = objectives
        out["G"] = constraints  # Constraint violations
        self.generation += 1


def run_optimization(template_path,
                    sim_dir,
                    variables_config,
                    pop_size=20,
                    n_generations=10,
                    objective_mode="EUR",
                    economics=None,
                    n_parallel=4,
                    simulator_command=None,
                    run_name=None,
                    save_comprehensive=True,
                    algorithm="GA",
                    algorithm_params=None,
                    timeout=600,
                    initial_population_file=None,
                    warm_start_fraction=0.4):
    """
    Run optimization using specified algorithm (GA or PSO)
    
    Parameters:
    -----------
    template_path : str
        Path to template .DATA file
    sim_dir : str
        Directory for simulation files
    timeout : int
        Simulation timeout in seconds (default: 600)
    variables_config : dict
        Variable definitions with bounds
    pop_size : int
        Population size for GA
    n_generations : int
        Number of generations
    objective_mode : str
        'EUR' or 'NPV'
    n_parallel : int
        Number of parallel simulations
    simulator_command : str, optional
        Custom simulator command with ${sim_file_path} placeholder
    run_name : str, optional
        Name for this optimization run
    save_comprehensive : bool
        If True, save comprehensive results (JSON + CSV)
    algorithm : str
        Optimization algorithm: "GA" or "PSO"
    algorithm_params : dict, optional
        Algorithm-specific parameters
    initial_population_file : str, optional
        Path to CSV file with initial population for warm-starting
        Format: CSV with variable columns (no headers for generation/individual/objective)
    warm_start_fraction : float
        Fraction of population to seed from initial_population_file (default: 0.4 = 40%)
        Remaining fraction filled with random individuals
        
    Returns:
    --------
    result : pymoo Result object
        Optimization result containing best solution
    """
    
    # Create results writer if comprehensive saving is enabled
    results_writer = None
    if save_comprehensive:
        from datetime import datetime
        if run_name is None:
            run_name = f"opt_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        results_writer = OptimizationResultsWriter(sim_dir, run_name)
        
        # Save configuration
        config_dict = {
            'template_path': template_path,
            'sim_dir': sim_dir,
            'variables_config': variables_config,
            'pop_size': pop_size,
            'n_generations': n_generations,
            'objective_mode': objective_mode,
            'n_parallel': n_parallel,
            'simulator_command': simulator_command,
            'algorithm': algorithm,
            'algorithm_params': algorithm_params or {}
        }
        results_writer.save_configuration(config_dict)
    
    # Create problem
    problem = ReservoirOptimizationProblem(
        template_path=template_path,
        sim_dir=sim_dir,
        variables_config=variables_config,
        objective_mode=objective_mode,
        economics=economics,
        n_parallel=n_parallel,
        simulator_command=simulator_command,
        results_writer=results_writer,
        timeout=timeout
    )
    
    # Set number of generations for progress tracking
    problem.n_generations = n_generations
    
    # Prepare sampling (warm-start or random)
    sampling_method = IntegerRandomSampling()
    
    if initial_population_file:
        try:
            from warm_start_sampling import HybridWarmStartSampling, load_initial_population_from_csv
            
            print("\n" + "="*60)
            print("WARM-START ENABLED")
            print("="*60)
            
            # Load initial population
            initial_pop = load_initial_population_from_csv(initial_population_file)
            
            print(f"  Loaded {len(initial_pop)} individuals from: {initial_population_file}")
            print(f"  Warm-start fraction: {warm_start_fraction*100:.0f}%")
            
            n_seed = int(pop_size * warm_start_fraction)
            n_random = pop_size - n_seed
            
            print(f"  Phase 3 population ({pop_size} total):")
            print(f"    • {n_seed} from Phase 2 ({warm_start_fraction*100:.0f}%)")
            print(f"    • {n_random} fresh random ({(1-warm_start_fraction)*100:.0f}%)")
            print(f"  Strategy: Balance knowledge exploitation with exploration")
            print("="*60 + "\n")
            
            # Create hybrid warm-start sampling
            sampling_method = HybridWarmStartSampling(
                initial_population=initial_pop,
                seed_fraction=warm_start_fraction
            )
            
        except Exception as e:
            print(f"Warning: Warm-start failed ({e}), using random initialization")
            sampling_method = IntegerRandomSampling()
    
    # Configure optimization algorithm
    if algorithm_params is None:
        algorithm_params = {}
    
    if algorithm.upper() == "PSO":
        # Particle Swarm Optimization
        print("\n" + "="*60)
        print("Starting Particle Swarm Optimization (PSO)")
        print("="*60 + "\n")
        
        # PSO parameters with defaults
        w = algorithm_params.get('w', 0.9)           # Inertia weight
        c1 = algorithm_params.get('c1', 2.0)         # Cognitive parameter
        c2 = algorithm_params.get('c2', 2.0)         # Social parameter
        adaptive = algorithm_params.get('adaptive', True)
        
        print(f"PSO Parameters:")
        print(f"  Inertia weight (w): {w}")
        print(f"  Cognitive parameter (c1): {c1}")
        print(f"  Social parameter (c2): {c2}")
        print(f"  Adaptive: {adaptive}\n")
        
        algo = PSO(
            pop_size=pop_size,
            sampling=sampling_method,
            w=w,
            c1=c1,
            c2=c2,
            adaptive=adaptive
        )
        
    else:  # Default to GA
        # Genetic Algorithm
        print("\n" + "="*60)
        print("Starting Genetic Algorithm Optimization (GA)")
        print("="*60 + "\n")
        
        # GA parameters with defaults
        crossover_prob = algorithm_params.get('crossover_prob', 0.9)
        crossover_eta = algorithm_params.get('crossover_eta', 15)
        mutation_prob = algorithm_params.get('mutation_prob', 0.1)
        mutation_eta = algorithm_params.get('mutation_eta', 20)
        
        print(f"GA Parameters:")
        print(f"  Crossover probability: {crossover_prob}")
        print(f"  Crossover eta: {crossover_eta}")
        print(f"  Mutation probability: {mutation_prob}")
        print(f"  Mutation eta: {mutation_eta}\n")
        
        algo = GA(
            pop_size=pop_size,
            sampling=sampling_method,
            crossover=SBX(prob=crossover_prob, eta=crossover_eta, vtype=float, repair=None),
            mutation=PM(prob=mutation_prob, eta=mutation_eta, vtype=float, repair=None),
            eliminate_duplicates=True
        )
    
    # Configure termination criterion
    termination = get_termination("n_gen", n_generations)
    
    result = minimize(
        problem,
        algo,
        termination,
        seed=42,
        verbose=True
    )
    
    # Print results
    print("\n" + "="*60)
    print("OPTIMIZATION COMPLETE")
    print("="*60)
    
    best_x = result.X
    best_obj = -result.F[0]  # Convert back to positive (we minimized negative)
    
    # Check if best solution has overlaps
    num_overlaps = problem._check_well_overlaps(best_x)
    
    # Display objective
    if objective_mode == "NPV":
        obj_display = f"${best_obj/1e6:.2f} MM"
    else:
        obj_display = f"{best_obj:.2f}"
    
    print(f"\nBest {objective_mode}: {obj_display}")
    
    # Display constraint satisfaction
    if num_overlaps == 0:
        print("✓ Solution is feasible (no well overlaps)")
    else:
        print(f"⚠️  Warning: Best solution has {num_overlaps} overlapping well(s)")
    
    # Show only optimized variables (those with min != max)
    var_dict = {name: int(val) for name, val in zip(problem.var_names, best_x)}
    optimized_vars = {k: v for k, v in var_dict.items() 
                     if variables_config[k]['min'] != variables_config[k]['max']}
    
    if len(optimized_vars) <= 20:  # Show all if reasonable number
        print("\nOptimized Variables:")
        for var_name, var_value in optimized_vars.items():
            print(f"  {var_name}: {var_value}")
    else:
        print(f"\n{len(optimized_vars)} variables optimized (see results file for details)")
    
    print("="*60 + "\n")
    
    # Save comprehensive results
    if save_comprehensive and results_writer:
        # Check if we have evaluations
        if results_writer.evaluations:
            # Find best individual info from evaluations
            best_eval = max(results_writer.evaluations, 
                           key=lambda e: e['objective'] if e['success'] else -float('inf'))
            
            best_individual = {
                'generation': best_eval['generation'],
                'individual': best_eval['individual'],
                'case_name': best_eval['case_name'],
                'variables': {k: v for k, v in best_eval.items() 
                             if k not in ['generation', 'individual', 'case_name', 'success', 'objective']},
                'objective': best_eval['objective']
            }
        else:
            # Fallback: construct from pymoo result
            print("Warning: No evaluations recorded, using pymoo result for best solution")
            best_individual = {
                'generation': -1,
                'individual': -1,
                'case_name': 'unknown',
                'variables': var_dict,
                'objective': best_obj
            }
        
        # Save all results
        results_writer.save_evaluations_table()
        
        results_writer.save_final_results(best_individual, result)
        
        print("\nComprehensive results saved:")
        print(f"  Configuration: {results_writer.config_file}")
        print(f"  Results JSON: {results_writer.results_file}")
        print(f"  Evaluations CSV: {results_writer.evaluations_file}")
        print(f"  Summary TXT: {results_writer.summary_file}")
        
        # Generate plots automatically
        print("\nGenerating optimization plots...")
        try:
            plot_optimization_progress(
                str(results_writer.evaluations_file),
                output_dir=None,  # Save in same directory as CSV
                show=False  # Don't try to display (we're in background)
            )
            plot_simple_progress(
                str(results_writer.evaluations_file),
                show=False
            )
            print(f"  Progress plot: {results_writer.evaluations_file.stem}_progress.png")
            print(f"  Simple plot: {results_writer.evaluations_file.stem}_simple.png")
        except Exception as e:
            print(f"  Warning: Could not generate plots: {e}")
        print()
    
    return result

