"""
Main simulation engine for the Dutch housing market model.

Coordinates all subsystems and runs the simulation.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import asdict

from .config import SimulationConfig, MarketState
from .population import PopulationDynamics
from .supply import HousingSupply
from .pricing import PriceMechanism
from .economics import Economics


class HousingMarketSimulator:
    """
    Main simulator coordinating all housing market components.

    Manages:
    - Population dynamics
    - Housing supply
    - Price mechanism
    - Economic conditions
    - Data collection and analysis
    """

    def __init__(self, config: Optional[SimulationConfig] = None):
        """
        Initialize simulator with configuration.

        Args:
            config: Simulation configuration (uses defaults if None)
        """
        self.config = config or SimulationConfig()

        # Initialize subsystems
        self.population = PopulationDynamics(self.config)
        self.supply = HousingSupply(self.config)
        self.pricing = PriceMechanism(self.config)
        self.economics = Economics(self.config)

        # Initialize state
        self.state = MarketState()

        # Data storage
        self.history: List[Dict] = []

        # Scenario tracking
        self.current_scenario = "baseline"

    def reset(self):
        """Reset simulation to initial conditions."""
        self.__init__(self.config)

    def set_immigration_scenario(self, scenario: str):
        """
        Set immigration scenario for the simulation.

        Args:
            scenario: One of 'low', 'baseline', 'high', 'very_high', 'crisis'
        """
        self.population.set_immigration_scenario(scenario)
        self.current_scenario = scenario

    def run(self, years: Optional[int] = None, verbose: bool = True) -> pd.DataFrame:
        """
        Run the simulation.

        Args:
            years: Number of years to simulate (uses config if None)
            verbose: Print progress updates

        Returns:
            DataFrame with simulation history
        """
        if years:
            total_timesteps = years * self.config.timesteps_per_year
        else:
            total_timesteps = self.config.total_timesteps

        if verbose:
            print(f"Starting simulation: {self.config.start_year} to {self.config.start_year + total_timesteps / self.config.timesteps_per_year:.0f}")
            print(f"Immigration scenario: {self.current_scenario}")
            print(f"Total timesteps: {total_timesteps}")
            print("-" * 60)

        for t in range(total_timesteps):
            self.step()

            # Progress updates
            if verbose and t % (self.config.timesteps_per_year * 5) == 0:
                progress = t / total_timesteps * 100
                print(f"Progress: {progress:.1f}% - Year {self.state.year:.1f} - "
                      f"Price: €{self.state.avg_price:,.0f} - "
                      f"Population: {self.state.population:,.0f}")

        if verbose:
            print("-" * 60)
            print("Simulation complete!")
            self._print_summary()

        return self.get_history_dataframe()

    def step(self):
        """Execute one simulation timestep."""
        # Update subsystems in order
        self.state = self.economics.update(self.state)
        self.state = self.population.update(self.state)
        self.state = self.supply.update(self.state)
        self.state = self.pricing.update(self.state)

        # Update timestep and year
        self.state.timestep += 1
        self.state.year = self.config.start_year + (
            self.state.timestep * self.config.timestep_months / 12
        )

        # Record history
        self._record_state()

    def _record_state(self):
        """Record current state to history."""
        state_dict = asdict(self.state)
        # Flatten regional prices
        state_dict['regional_prices_str'] = str(state_dict['regional_prices'])
        state_dict.pop('regional_prices')
        # Add computed properties
        state_dict['housing_shortage_pct'] = self.state.housing_shortage_pct
        state_dict['occupancy_rate'] = self.state.occupancy_rate
        self.history.append(state_dict)

    def get_history_dataframe(self) -> pd.DataFrame:
        """
        Get simulation history as pandas DataFrame.

        Returns:
            DataFrame with all historical states
        """
        return pd.DataFrame(self.history)

    def _print_summary(self):
        """Print summary statistics from the simulation."""
        initial = self.history[0]
        final = self.history[-1]

        print("\n" + "=" * 60)
        print("SIMULATION SUMMARY")
        print("=" * 60)

        print(f"\nScenario: {self.current_scenario}")
        print(f"Period: {initial['year']:.1f} - {final['year']:.1f}")

        print("\n--- POPULATION ---")
        print(f"Initial: {initial['population']:,.0f}")
        print(f"Final: {final['population']:,.0f}")
        print(f"Change: {(final['population'] - initial['population']) / initial['population'] * 100:+.1f}%")
        print(f"Immigrant population: {final['immigrant_population']:,.0f} ({final['immigrant_population']/final['population']*100:.1f}%)")

        print("\n--- HOUSING STOCK ---")
        print(f"Initial: {initial['total_housing']:,} units")
        print(f"Final: {final['total_housing']:,} units")
        print(f"Change: {(final['total_housing'] - initial['total_housing']) / initial['total_housing'] * 100:+.1f}%")
        print(f"Shortage: {final['shortage']:,.0f} units ({final['housing_shortage_pct']:.1f}%)")

        print("\n--- PRICES ---")
        print(f"Initial: €{initial['avg_price']:,.0f}")
        print(f"Final: €{final['avg_price']:,.0f}")
        print(f"Change: {(final['avg_price'] - initial['avg_price']) / initial['avg_price'] * 100:+.1f}%")
        print(f"Price index: {final['price_index']:.1f}")

        print("\n--- AFFORDABILITY ---")
        print(f"Initial price-to-income: {initial['affordability_ratio']:.1f}x")
        print(f"Final price-to-income: {final['affordability_ratio']:.1f}x")

        burden = self.pricing.calculate_housing_cost_burden(self.state)
        print(f"Housing cost burden: {burden:.1f}% of income")

        print("\n--- MARKET CONDITIONS ---")
        print(f"Market temperature: {self.pricing.get_market_temperature(self.state)}")
        print(f"Interest rate: {final['interest_rate']*100:.2f}%")
        print(f"GDP index: {final['gdp_index']:.1f}")

        print("=" * 60)

    def compare_scenarios(
        self,
        scenarios: List[str],
        years: int = 30,
        verbose: bool = False
    ) -> Dict[str, pd.DataFrame]:
        """
        Run and compare multiple immigration scenarios.

        Args:
            scenarios: List of scenario names to compare
            years: Number of years to simulate
            verbose: Print progress for each scenario

        Returns:
            Dictionary mapping scenario names to their history DataFrames
        """
        results = {}

        print(f"\nRunning {len(scenarios)} scenarios...")
        print("=" * 60)

        for scenario in scenarios:
            print(f"\n>>> Scenario: {scenario.upper()}")
            self.reset()
            self.set_immigration_scenario(scenario)
            df = self.run(years=years, verbose=verbose)
            results[scenario] = df

            # Quick summary
            final_price = df['avg_price'].iloc[-1]
            initial_price = df['avg_price'].iloc[0]
            price_change = (final_price - initial_price) / initial_price * 100
            print(f"    Final price: €{final_price:,.0f} ({price_change:+.1f}%)")
            print(f"    Final population: {df['population'].iloc[-1]:,.0f}")

        print("\n" + "=" * 60)
        print("All scenarios complete!")

        return results

    def get_key_metrics(self) -> Dict[str, float]:
        """
        Get key metrics from the final state.

        Returns:
            Dictionary of key metrics
        """
        if not self.history:
            return {}

        final = self.history[-1]
        initial = self.history[0]

        return {
            'final_price': final['avg_price'],
            'price_change_pct': (final['avg_price'] - initial['avg_price']) / initial['avg_price'] * 100,
            'final_population': final['population'],
            'population_change_pct': (final['population'] - initial['population']) / initial['population'] * 100,
            'final_shortage': final['shortage'],
            'shortage_pct': final['housing_shortage_pct'],
            'affordability_ratio': final['affordability_ratio'],
            'housing_stock': final['total_housing'],
            'immigrant_share': final['immigrant_population'] / final['population'] * 100,
        }

    def analyze_immigration_impact(self, baseline_scenario: str = 'baseline') -> pd.DataFrame:
        """
        Analyze the impact of immigration by comparing scenarios.

        Args:
            baseline_scenario: Reference scenario for comparison

        Returns:
            DataFrame with comparative analysis
        """
        scenarios = ['low', 'baseline', 'high', 'very_high']
        results = self.compare_scenarios(scenarios, years=30, verbose=False)

        # Extract final metrics
        comparison = []
        for scenario, df in results.items():
            final = df.iloc[-1]
            initial = df.iloc[0]

            comparison.append({
                'scenario': scenario,
                'immigration_multiplier': self.config.immigration_scenarios[scenario],
                'final_price': final['avg_price'],
                'price_change_pct': (final['avg_price'] - initial['avg_price']) / initial['avg_price'] * 100,
                'final_population': final['population'],
                'population_change_pct': (final['population'] - initial['population']) / initial['population'] * 100,
                'final_shortage': final['shortage'],
                'affordability_ratio': final['affordability_ratio'],
            })

        comparison_df = pd.DataFrame(comparison)

        # Calculate differences relative to baseline
        baseline_row = comparison_df[comparison_df['scenario'] == baseline_scenario].iloc[0]

        comparison_df['price_diff_from_baseline'] = (
            comparison_df['final_price'] - baseline_row['final_price']
        )
        comparison_df['price_diff_pct'] = (
            comparison_df['price_diff_from_baseline'] / baseline_row['final_price'] * 100
        )

        return comparison_df
