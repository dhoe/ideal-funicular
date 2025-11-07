#!/usr/bin/env python3
"""Debug script to understand what's happening in the simulation."""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from housing_simulation.simulator import HousingMarketSimulator

sim = HousingMarketSimulator()

print("Initial state:")
print(f"  Population: {sim.state.population:,.0f}")
print(f"  Households: {sim.state.households:,.0f}")
print(f"  Total housing: {sim.state.total_housing:,}")
print(f"  Vacant: {sim.state.vacant:,}")
print(f"  Price: €{sim.state.avg_price:,.0f}")
print(f"  Interest rate: {sim.state.interest_rate*100:.2f}%")
print()

print("Running 12 months...")
for i in range(12):
    sim.step()
    if i < 3 or i == 11:
        print(f"\nMonth {i+1}:")
        print(f"  Supply: {sim.state.supply:.1f}, Demand: {sim.state.demand:.1f}")
        print(f"  Shortage: {sim.state.shortage:.1f}")
        print(f"  Price: €{sim.state.avg_price:,.0f}")
        print(f"  Population: {sim.state.population:,.0f}")
        print(f"  Households: {sim.state.households:,.0f}")
