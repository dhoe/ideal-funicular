#!/usr/bin/env python3
"""
Example script to run the Dutch housing market simulation.

This script demonstrates how to:
1. Run a single simulation scenario
2. Compare multiple immigration scenarios
3. Generate visualizations
4. Export results
"""

import sys
import os

# Add housing_simulation to path
sys.path.insert(0, os.path.dirname(__file__))

from housing_simulation.simulator import HousingMarketSimulator
from housing_simulation.visualization import Visualizer
from housing_simulation.config import SimulationConfig


def main():
    """Run the main simulation and analysis."""

    print("=" * 70)
    print("DUTCH HOUSING MARKET SIMULATION")
    print("Analyzing the Effect of Immigration on Housing Prices")
    print("=" * 70)

    # Create simulator with default configuration
    sim = HousingMarketSimulator()

    # Option 1: Run a single scenario
    print("\n--- Running Baseline Scenario ---\n")
    sim.set_immigration_scenario('baseline')
    df_baseline = sim.run(years=30, verbose=True)

    # Save results
    df_baseline.to_csv('results_baseline.csv', index=False)
    print("\nResults saved to: results_baseline.csv")

    # Create visualizations
    print("\nGenerating visualizations...")
    viz = Visualizer()
    viz.plot_simulation_overview(df_baseline, scenario='baseline', save_path='simulation_baseline.png')

    # Option 2: Compare multiple scenarios
    print("\n\n" + "=" * 70)
    print("SCENARIO COMPARISON")
    print("=" * 70)

    scenarios = ['low', 'baseline', 'high', 'very_high']
    results = sim.compare_scenarios(scenarios, years=30, verbose=False)

    # Create comparison plots
    print("\nGenerating comparison visualizations...")
    viz.plot_scenario_comparison(results, save_path='comparison_scenarios.png')

    # Detailed immigration impact analysis
    print("\n\n" + "=" * 70)
    print("IMMIGRATION IMPACT ANALYSIS")
    print("=" * 70)

    comparison_df = sim.analyze_immigration_impact()
    print("\n", comparison_df.to_string(index=False))

    viz.plot_immigration_impact_analysis(comparison_df, save_path='immigration_impact.png')

    # Create summary table
    summary = viz.create_summary_table(results)
    print("\n\n--- SUMMARY TABLE ---")
    print(summary.to_string(index=False))

    # Save summary
    summary.to_csv('summary_table.csv', index=False)
    print("\n\nSummary saved to: summary_table.csv")

    # Create price heatmap
    print("\nGenerating price heatmap...")
    viz.plot_price_heatmap(results, save_path='price_heatmap.png')

    print("\n" + "=" * 70)
    print("SIMULATION COMPLETE!")
    print("=" * 70)
    print("\nGenerated files:")
    print("  - results_baseline.csv")
    print("  - simulation_baseline.png")
    print("  - comparison_scenarios.png")
    print("  - immigration_impact.png")
    print("  - summary_table.csv")
    print("  - price_heatmap.png")
    print("\n")


if __name__ == "__main__":
    main()
