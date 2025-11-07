#!/usr/bin/env python3
"""Run a 10-year simulation across multiple immigration scenarios."""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from housing_simulation.simulator import HousingMarketSimulator
from housing_simulation.visualization import Visualizer

print("=" * 70)
print("DUTCH HOUSING MARKET SIMULATION - 10 YEAR PROJECTION")
print("Analyzing Immigration Effects on Housing Prices")
print("=" * 70)

# Run multiple scenarios
sim = HousingMarketSimulator()
scenarios = ['low', 'baseline', 'high', 'very_high']

print("\nRunning scenarios:", scenarios)
results = sim.compare_scenarios(scenarios, years=10, verbose=False)

print("\n" + "=" * 70)
print("DETAILED RESULTS")
print("=" * 70)

for scenario, df in results.items():
    initial = df.iloc[0]
    final = df.iloc[-1]

    print(f"\n--- {scenario.upper()} IMMIGRATION SCENARIO ---")
    print(f"Immigration multiplier: {sim.config.immigration_scenarios[scenario]}x")

    print(f"\nPopulation:")
    print(f"  Initial: {initial['population']:,.0f}")
    print(f"  Final: {final['population']:,.0f}")
    print(f"  Change: {(final['population'] - initial['population']):,.0f} ({(final['population']/initial['population'] - 1)*100:+.1f}%)")
    print(f"  Immigrant population: {final['immigrant_population']:,.0f} ({final['immigrant_population']/final['population']*100:.1f}%)")

    print(f"\nHousing:")
    print(f"  Total stock: {final['total_housing']:,} units")
    print(f"  Households: {final['households']:,.0f}")
    print(f"  Shortage: {final['shortage']:,.0f} units")

    print(f"\nPrices:")
    print(f"  Initial: €{initial['avg_price']:,.0f}")
    print(f"  Final: €{final['avg_price']:,.0f}")
    print(f"  Change: {(final['avg_price'] - initial['avg_price']):,.0f} ({(final['avg_price']/initial['avg_price'] - 1)*100:+.1f}%)")
    print(f"  Price Index: {final['price_index']:.1f}")

    print(f"\nAffordability:")
    print(f"  Initial P/I ratio: {initial['affordability_ratio']:.1f}x")
    print(f"  Final P/I ratio: {final['affordability_ratio']:.1f}x")

# Create comparison analysis
print("\n" + "=" * 70)
print("IMMIGRATION IMPACT COMPARISON")
print("=" * 70)

baseline_final = results['baseline'].iloc[-1]
print(f"\nBaseline final price: €{baseline_final['avg_price']:,.0f}\n")

for scenario in scenarios:
    if scenario == 'baseline':
        continue
    final = results[scenario].iloc[-1]
    price_diff = final['avg_price'] - baseline_final['avg_price']
    price_diff_pct = price_diff / baseline_final['avg_price'] * 100
    pop_diff = final['population'] - baseline_final['population']

    print(f"{scenario.upper()} vs BASELINE:")
    print(f"  Price difference: €{price_diff:,.0f} ({price_diff_pct:+.1f}%)")
    print(f"  Population difference: {pop_diff:,.0f}")
    print(f"  Shortage difference: {final['shortage'] - baseline_final['shortage']:,.0f} units")
    print()

# Generate visualizations
print("Generating visualizations...")
viz = Visualizer()

# Individual scenario plots
for scenario, df in results.items():
    viz.plot_simulation_overview(df, scenario=scenario, save_path=f'sim_10yr_{scenario}.png')

# Comparison plot
viz.plot_scenario_comparison(results, save_path='sim_10yr_comparison.png')

# Impact analysis
sim.reset()
comparison_df = sim.analyze_immigration_impact()
viz.plot_immigration_impact_analysis(comparison_df, save_path='sim_10yr_impact.png')

print("\n" + "=" * 70)
print("SIMULATION COMPLETE!")
print("=" * 70)
print("\nGenerated files:")
for scenario in scenarios:
    print(f"  - sim_10yr_{scenario}.png")
print("  - sim_10yr_comparison.png")
print("  - sim_10yr_impact.png")
print()
