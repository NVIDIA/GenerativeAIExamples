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
Plot optimization progress from evaluations CSV

Creates plots showing:
1. Objective value vs simulation number
2. Best-so-far progression
3. Generation-wise box plots
"""

import sys
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path


def plot_optimization_progress(csv_file, output_dir=None, show=True):
    """
    Plot optimization progress from evaluations CSV
    
    Parameters:
    -----------
    csv_file : str
        Path to evaluations CSV file
    output_dir : str, optional
        Directory to save plots (default: same as CSV)
    show : bool
        Whether to display plots interactively
    """
    # Read CSV
    df = pd.read_csv(csv_file)
    
    # Filter successful evaluations
    df_success = df[df['success'] == True].copy()
    
    if len(df_success) == 0:
        print("No successful evaluations found!")
        return
    
    # Add cumulative simulation number
    df_success['sim_number'] = range(1, len(df_success) + 1)
    
    # Calculate best-so-far
    df_success['best_so_far'] = df_success['objective'].cummax()
    
    # Get objective name from parent directory or default
    csv_path = Path(csv_file)
    if output_dir is None:
        output_dir = csv_path.parent
    else:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
    
    # Try to infer objective name
    objective_name = "Objective"
    try:
        # Check if there's a config file nearby
        config_files = list(csv_path.parent.glob("*_config.json"))
        if config_files:
            import json
            with open(config_files[0], 'r') as f:
                config = json.load(f)
                objective_mode = config.get('objective_mode', 'EUR')
                objective_name = objective_mode
    except:
        pass
    
    # Create figure with subplots
    fig = plt.figure(figsize=(16, 10))
    
    # Plot 1: All evaluations
    ax1 = plt.subplot(2, 2, 1)
    ax1.scatter(df_success['sim_number'], df_success['objective'], 
                alpha=0.6, s=50, c='steelblue', edgecolors='black', linewidth=0.5)
    ax1.plot(df_success['sim_number'], df_success['best_so_far'], 
             'r-', linewidth=2, label='Best so far')
    ax1.set_xlabel('Simulation Number', fontsize=12)
    ax1.set_ylabel(f'{objective_name}', fontsize=12)
    ax1.set_title('Optimization Progress: All Evaluations', fontsize=14, fontweight='bold')
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3)
    
    # Add generation boundaries
    for gen in df_success['generation'].unique()[1:]:
        first_sim = df_success[df_success['generation'] == gen]['sim_number'].iloc[0]
        ax1.axvline(x=first_sim, color='gray', linestyle='--', alpha=0.5, linewidth=1)
    
    # Plot 2: Best so far only
    ax2 = plt.subplot(2, 2, 2)
    ax2.plot(df_success['sim_number'], df_success['best_so_far'], 
             'g-o', linewidth=2, markersize=4, markerfacecolor='green', markeredgecolor='darkgreen')
    ax2.fill_between(df_success['sim_number'], 
                      df_success['best_so_far'].min(), 
                      df_success['best_so_far'],
                      alpha=0.3, color='green')
    ax2.set_xlabel('Simulation Number', fontsize=12)
    ax2.set_ylabel(f'Best {objective_name}', fontsize=12)
    ax2.set_title('Best Solution Found Over Time', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    
    # Add improvement annotations
    improvements = df_success[df_success['objective'] == df_success['best_so_far']]
    for idx, row in improvements.iterrows():
        if row['sim_number'] > 1:  # Skip first
            ax2.annotate(f"{row['objective']:.2f}", 
                        xy=(row['sim_number'], row['best_so_far']),
                        xytext=(5, 5), textcoords='offset points',
                        fontsize=8, color='darkgreen',
                        bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7))
    
    # Plot 3: Generation-wise box plot
    ax3 = plt.subplot(2, 2, 3)
    generations = sorted(df_success['generation'].unique())
    gen_data = [df_success[df_success['generation'] == gen]['objective'].values 
                for gen in generations]
    
    bp = ax3.boxplot(gen_data, tick_labels=[f"Gen {g}" for g in generations],
                     patch_artist=True, showmeans=True)
    
    # Color boxes
    colors = plt.cm.viridis(np.linspace(0, 1, len(generations)))
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    
    ax3.set_xlabel('Generation', fontsize=12)
    ax3.set_ylabel(f'{objective_name}', fontsize=12)
    ax3.set_title('Distribution per Generation', fontsize=14, fontweight='bold')
    ax3.grid(True, alpha=0.3, axis='y')
    
    # Plot 4: Improvement rate
    ax4 = plt.subplot(2, 2, 4)
    
    # Calculate improvement from previous best
    improvement = df_success['best_so_far'].diff().fillna(0)
    improvement_pct = (improvement / df_success['best_so_far'].shift(1) * 100).fillna(0)
    
    # Plot improvement bars
    colors_imp = ['green' if x > 0 else 'lightgray' for x in improvement]
    ax4.bar(df_success['sim_number'], improvement, color=colors_imp, alpha=0.7, edgecolor='black', linewidth=0.5)
    ax4.set_xlabel('Simulation Number', fontsize=12)
    ax4.set_ylabel(f'Improvement in {objective_name}', fontsize=12)
    ax4.set_title('Improvement at Each Step', fontsize=14, fontweight='bold')
    ax4.grid(True, alpha=0.3, axis='y')
    ax4.axhline(y=0, color='black', linestyle='-', linewidth=1)
    
    # Add generation boundaries
    for gen in df_success['generation'].unique()[1:]:
        first_sim = df_success[df_success['generation'] == gen]['sim_number'].iloc[0]
        ax4.axvline(x=first_sim, color='gray', linestyle='--', alpha=0.5, linewidth=1)
    
    plt.tight_layout()
    
    # Save figure
    output_file = output_dir / f"{csv_path.stem}_progress.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Progress plot saved to: {output_file}")
    
    # Show if requested
    if show:
        plt.show()
    else:
        plt.close()
    
    return fig


def plot_simple_progress(csv_file, output_file=None, show=True):
    """
    Simple plot: objective vs simulation number with best-so-far line
    
    Parameters:
    -----------
    csv_file : str
        Path to evaluations CSV file
    output_file : str, optional
        Output file path for plot
    show : bool
        Whether to display plot interactively
    """
    # Read CSV
    df = pd.read_csv(csv_file)
    df_success = df[df['success'] == True].copy()
    
    if len(df_success) == 0:
        print("No successful evaluations found!")
        return
    
    # Add simulation number and best-so-far
    df_success['sim_number'] = range(1, len(df_success) + 1)
    df_success['best_so_far'] = df_success['objective'].cummax()
    
    # Get objective name
    objective_name = "Objective"
    try:
        csv_path = Path(csv_file)
        config_files = list(csv_path.parent.glob("*_config.json"))
        if config_files:
            import json
            with open(config_files[0], 'r') as f:
                config = json.load(f)
                objective_name = config.get('objective_mode', 'EUR')
    except:
        pass
    
    # Create plot
    plt.figure(figsize=(12, 6))
    
    # Plot all evaluations
    plt.scatter(df_success['sim_number'], df_success['objective'], 
                alpha=0.6, s=80, c='steelblue', edgecolors='black', 
                linewidth=0.5, label='Evaluations', zorder=2)
    
    # Plot best-so-far line
    plt.plot(df_success['sim_number'], df_success['best_so_far'], 
             'r-', linewidth=3, label='Best so far', zorder=3)
    
    # Mark best solution
    best_idx = df_success['objective'].idxmax()
    best_row = df_success.loc[best_idx]
    plt.scatter([best_row['sim_number']], [best_row['objective']],
                s=300, c='gold', marker='*', edgecolors='red', 
                linewidth=2, label=f'Best: {best_row["objective"]:.2f}', zorder=4)
    
    # Add generation boundaries
    for gen in df_success['generation'].unique()[1:]:
        first_sim = df_success[df_success['generation'] == gen]['sim_number'].iloc[0]
        plt.axvline(x=first_sim, color='gray', linestyle='--', 
                   alpha=0.5, linewidth=1.5, zorder=1)
    
    # Labels and formatting
    plt.xlabel('Simulation Number', fontsize=14, fontweight='bold')
    plt.ylabel(f'{objective_name}', fontsize=14, fontweight='bold')
    plt.title('Optimization Progress', fontsize=16, fontweight='bold')
    plt.legend(fontsize=12, loc='lower right')
    plt.grid(True, alpha=0.3)
    
    # Add statistics text box
    stats_text = f"""Statistics:
Total Simulations: {len(df_success)}
Best {objective_name}: {df_success['objective'].max():.4f}
Mean {objective_name}: {df_success['objective'].mean():.4f}
Improvement: {df_success['objective'].max() - df_success['objective'].iloc[0]:.4f}
"""
    plt.text(0.02, 0.98, stats_text, transform=plt.gca().transAxes,
            fontsize=10, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    plt.tight_layout()
    
    # Save if output file specified
    if output_file is None:
        csv_path = Path(csv_file)
        output_file = csv_path.parent / f"{csv_path.stem}_simple.png"
    
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Simple progress plot saved to: {output_file}")
    
    # Show if requested
    if show:
        plt.show()
    else:
        plt.close()


def print_summary(csv_file):
    """Print summary statistics from evaluations CSV"""
    df = pd.read_csv(csv_file)
    df_success = df[df['success'] == True]
    
    print("\n" + "="*60)
    print("OPTIMIZATION SUMMARY")
    print("="*60)
    
    print(f"\nTotal evaluations: {len(df)}")
    print(f"Successful: {len(df_success)}")
    print(f"Failed: {len(df) - len(df_success)}")
    
    if len(df_success) > 0:
        print(f"\nObjective Statistics:")
        print(f"  Best: {df_success['objective'].max():.4f}")
        print(f"  Mean: {df_success['objective'].mean():.4f}")
        print(f"  Worst: {df_success['objective'].min():.4f}")
        print(f"  Std: {df_success['objective'].std():.4f}")
        
        # Best solution
        best_idx = df_success['objective'].idxmax()
        best = df_success.loc[best_idx]
        print(f"\nBest Solution:")
        print(f"  Generation: {int(best['generation'])}")
        print(f"  Individual: {int(best['individual'])}")
        print(f"  Case: {best['case_name']}")
        print(f"  Objective: {best['objective']:.4f}")
        
        # Print variable values (all columns except standard ones)
        var_cols = [col for col in df_success.columns 
                   if col not in ['generation', 'individual', 'case_name', 'success', 'objective']]
        if var_cols:
            print(f"  Variables:")
            for col in var_cols:
                print(f"    {col}: {best[col]}")
        
        # Generation statistics
        print(f"\nPer Generation:")
        for gen in sorted(df_success['generation'].unique()):
            gen_data = df_success[df_success['generation'] == gen]
            print(f"  Gen {int(gen)}: Best={gen_data['objective'].max():.4f}, "
                  f"Mean={gen_data['objective'].mean():.4f}, "
                  f"Count={len(gen_data)}")
    
    print("="*60 + "\n")


if __name__ == "__main__":
    """
    Usage:
        python plot_progress.py evaluations.csv
        python plot_progress.py evaluations.csv --simple
        python plot_progress.py evaluations.csv --no-show
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Plot optimization progress from evaluations CSV')
    parser.add_argument('csv_file', help='Path to evaluations CSV file')
    parser.add_argument('--simple', action='store_true', 
                       help='Create simple plot only (one figure)')
    parser.add_argument('--no-show', action='store_true',
                       help='Save plots without displaying')
    parser.add_argument('--output-dir', '-o', 
                       help='Output directory for plots (default: same as CSV)')
    parser.add_argument('--summary', action='store_true',
                       help='Print summary statistics only (no plots)')
    
    args = parser.parse_args()
    
    # Check file exists
    if not Path(args.csv_file).exists():
        print(f"Error: File not found: {args.csv_file}")
        sys.exit(1)
    
    # Print summary
    print_summary(args.csv_file)
    
    # Create plots
    if not args.summary:
        show = not args.no_show
        
        if args.simple:
            plot_simple_progress(args.csv_file, show=show)
        else:
            plot_optimization_progress(args.csv_file, 
                                      output_dir=args.output_dir, 
                                      show=show)
            plot_simple_progress(args.csv_file, show=show)

