#!/usr/bin/env python3
"""
Example script demonstrating custom scenarios and advanced usage.

This shows how to:
1. Create custom configuration
2. Test policy interventions
3. Run sensitivity analysis
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from housing_simulation.simulator import HousingMarketSimulator
from housing_simulation.config import SimulationConfig
from housing_simulation.visualization import Visualizer
import matplotlib.pyplot as plt


def scenario_high_construction():
    """Scenario: High immigration + Aggressive construction policy."""

    print("\n" + "=" * 70)
    print("SCENARIO: High Immigration + Aggressive Construction")
    print("=" * 70)

    # Create two simulations for comparison
    config = SimulationConfig()

    # Simulation 1: High immigration, normal construction
    sim1 = HousingMarketSimulator(config)
    sim1.set_immigration_scenario('high')
    df1 = sim1.run(years=30, verbose=False)

    # Simulation 2: High immigration, 50% more construction
    sim2 = HousingMarketSimulator(config)
    sim2.set_immigration_scenario('high')
    sim2.supply.set_construction_policy(1.5)  # 50% boost to construction
    df2 = sim2.run(years=30, verbose=False)

    # Compare results
    print("\n--- Without Construction Policy ---")
    print(f"Final price: €{df1['avg_price'].iloc[-1]:,.0f}")
    print(f"Price change: {(df1['avg_price'].iloc[-1] / df1['avg_price'].iloc[0] - 1) * 100:+.1f}%")
    print(f"Housing shortage: {df1['shortage'].iloc[-1]:,.0f} units")

    print("\n--- With Aggressive Construction ---")
    print(f"Final price: €{df2['avg_price'].iloc[-1]:,.0f}")
    print(f"Price change: {(df2['avg_price'].iloc[-1] / df2['avg_price'].iloc[0] - 1) * 100:+.1f}%")
    print(f"Housing shortage: {df2['shortage'].iloc[-1]:,.0f} units")

    # Visualize
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    axes[0].plot(df1['year'], df1['avg_price'] / 1000, label='Normal Construction', linewidth=2)
    axes[0].plot(df2['year'], df2['avg_price'] / 1000, label='50% More Construction', linewidth=2)
    axes[0].set_xlabel('Year')
    axes[0].set_ylabel('Average Price (€1000s)')
    axes[0].set_title('Effect of Construction Policy on Prices')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(df1['year'], df1['shortage'], label='Normal Construction', linewidth=2)
    axes[1].plot(df2['year'], df2['shortage'], label='50% More Construction', linewidth=2)
    axes[1].axhline(y=0, color='gray', linestyle='--', alpha=0.5)
    axes[1].set_xlabel('Year')
    axes[1].set_ylabel('Housing Shortage (units)')
    axes[1].set_title('Effect of Construction Policy on Shortage')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('policy_comparison.png', dpi=300, bbox_inches='tight')
    print("\nPlot saved to: policy_comparison.png")


def scenario_economic_crisis():
    """Scenario: Immigration + Economic crisis."""

    print("\n" + "=" * 70)
    print("SCENARIO: High Immigration During Economic Crisis")
    print("=" * 70)

    config = SimulationConfig()
    sim = HousingMarketSimulator(config)
    sim.set_immigration_scenario('high')

    # Trigger economic crisis after 10 years
    print("\nRunning simulation with economic crisis in year 2030...")

    # Run year by year to inject crisis
    for year in range(30):
        if year == 10:
            print(">>> Triggering economic crisis!")
            sim.economics.trigger_shock(severity=0.20, duration_months=18)

        sim.run(years=1, verbose=False)

    df = sim.get_history_dataframe()

    # Analyze impact
    print("\n--- Results ---")
    crisis_start_idx = 10 * 12
    pre_crisis_price = df['avg_price'].iloc[crisis_start_idx]
    crisis_bottom_price = df['avg_price'].iloc[crisis_start_idx:crisis_start_idx+24].min()
    final_price = df['avg_price'].iloc[-1]

    print(f"Price before crisis: €{pre_crisis_price:,.0f}")
    print(f"Lowest price during crisis: €{crisis_bottom_price:,.0f} ({(crisis_bottom_price/pre_crisis_price - 1)*100:+.1f}%)")
    print(f"Final price (20 years later): €{final_price:,.0f} ({(final_price/pre_crisis_price - 1)*100:+.1f}%)")

    # Plot
    viz = Visualizer()
    fig = viz.plot_simulation_overview(df, scenario='crisis', save_path='crisis_scenario.png')
    print("\nPlot saved to: crisis_scenario.png")


def sensitivity_analysis():
    """Run sensitivity analysis on key parameters."""

    print("\n" + "=" * 70)
    print("SENSITIVITY ANALYSIS")
    print("Testing sensitivity to construction delays")
    print("=" * 70)

    delays = [12, 24, 36, 48]  # months
    results = {}

    for delay in delays:
        print(f"\nTesting with {delay}-month construction delay...")
        config = SimulationConfig(construction_delay_months=delay)
        sim = HousingMarketSimulator(config)
        sim.set_immigration_scenario('high')
        df = sim.run(years=30, verbose=False)
        results[f"{delay}mo"] = df

    # Plot comparison
    fig, ax = plt.subplots(figsize=(12, 6))

    for label, df in results.items():
        ax.plot(df['year'], df['avg_price'] / 1000, label=f"{label} delay", linewidth=2)

    ax.set_xlabel('Year')
    ax.set_ylabel('Average Price (€1000s)')
    ax.set_title('Sensitivity to Construction Delay Duration')
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('sensitivity_construction_delay.png', dpi=300, bbox_inches='tight')
    print("\nPlot saved to: sensitivity_construction_delay.png")

    # Print summary
    print("\n--- Summary ---")
    for label, df in results.items():
        final_price = df['avg_price'].iloc[-1]
        initial_price = df['avg_price'].iloc[0]
        change = (final_price - initial_price) / initial_price * 100
        print(f"{label}: Final price €{final_price:,.0f} ({change:+.1f}%)")


def main():
    """Run all custom scenarios."""

    # Scenario 1: Construction policy
    scenario_high_construction()

    # Scenario 2: Economic crisis
    scenario_economic_crisis()

    # Scenario 3: Sensitivity analysis
    sensitivity_analysis()

    print("\n" + "=" * 70)
    print("ALL SCENARIOS COMPLETE!")
    print("=" * 70)


if __name__ == "__main__":
    main()
