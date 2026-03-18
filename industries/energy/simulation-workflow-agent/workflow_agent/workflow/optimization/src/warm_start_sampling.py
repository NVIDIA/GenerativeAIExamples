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
Custom pymoo sampling for warm-starting optimization with known good solutions
"""

import numpy as np
from pymoo.core.sampling import Sampling


class WarmStartSampling(Sampling):
    """
    Pymoo sampling that combines provided initial individuals with random sampling.
    
    Useful for warm-starting Phase 3 with Phase 2 results.
    
    Parameters
    ----------
    initial_population : np.ndarray
        Array of shape (n_initial, n_vars) with initial individuals
    """
    
    def __init__(self, initial_population: np.ndarray):
        super().__init__()
        self.initial_population = initial_population
        self.n_initial = len(initial_population)
    
    def _do(self, problem, n_samples, **kwargs):
        """
        Generate population combining initial individuals and random samples.
        
        Parameters
        ----------
        problem : Problem
            Pymoo problem instance
        n_samples : int
            Total number of samples needed
            
        Returns
        -------
        np.ndarray
            Population array of shape (n_samples, n_vars)
        """
        n_vars = problem.n_var
        xl = problem.xl  # Lower bounds
        xu = problem.xu  # Upper bounds
        
        # If we have exactly the right number of initial individuals, use them
        if self.n_initial == n_samples:
            return self.initial_population.copy()
        
        # If we have fewer initial individuals than needed
        if self.n_initial < n_samples:
            # Use all initial individuals + fill remaining with random
            n_random = n_samples - self.n_initial
            
            # Generate random individuals
            random_population = xl + np.random.random((n_random, n_vars)) * (xu - xl)
            
            # Combine
            population = np.vstack([
                self.initial_population,
                random_population
            ])
            
            return population
        
        # If we have more initial individuals than needed
        # Take the first n_samples (assumed to be sorted by quality)
        return self.initial_population[:n_samples].copy()


class HybridWarmStartSampling(Sampling):
    """
    Pymoo sampling that mixes initial individuals with random samples at specified ratio.
    
    Example: 40% from Phase 2, 60% fresh random
    
    Parameters
    ----------
    initial_population : np.ndarray
        Array of shape (n_initial, n_vars) with initial individuals (sorted by quality)
    seed_fraction : float
        Fraction of population to seed from initial_population (default: 0.4 = 40%)
    """
    
    def __init__(self, initial_population: np.ndarray, seed_fraction: float = 0.4):
        super().__init__()
        self.initial_population = initial_population
        self.seed_fraction = seed_fraction
        
        # Validate
        if not 0 < seed_fraction < 1:
            raise ValueError(f"seed_fraction must be in (0, 1), got {seed_fraction}")
    
    def _do(self, problem, n_samples, **kwargs):
        """
        Generate hybrid population.
        
        Parameters
        ----------
        problem : Problem
            Pymoo problem instance
        n_samples : int
            Total number of samples needed
            
        Returns
        -------
        np.ndarray
            Population array of shape (n_samples, n_vars)
        """
        n_vars = problem.n_var
        xl = problem.xl
        xu = problem.xu
        
        # Calculate split
        n_seed = int(n_samples * self.seed_fraction)
        n_random = n_samples - n_seed
        
        # Take top n_seed from initial population
        if len(self.initial_population) >= n_seed:
            seed_population = self.initial_population[:n_seed].copy()
        else:
            # Not enough initial individuals, use all we have
            seed_population = self.initial_population.copy()
            n_seed_actual = len(seed_population)
            n_random = n_samples - n_seed_actual
        
        # Generate random individuals
        random_population = xl + np.random.random((n_random, n_vars)) * (xu - xl)
        
        # Combine: seed first, then random
        population = np.vstack([seed_population, random_population])
        
        return population


def load_initial_population_from_csv(csv_file: str, n_individuals: int = None) -> np.ndarray:
    """
    Load initial population from CSV file.
    
    Parameters
    ----------
    csv_file : str
        Path to saved initial population CSV
    n_individuals : int, optional
        Number of individuals to load (default: all)
        
    Returns
    -------
    np.ndarray
        Population array
    """
    import pandas as pd
    
    df = pd.read_csv(csv_file)
    
    if n_individuals is not None:
        df = df.head(n_individuals)
    
    return df.values

