"""
Population dynamics module for the housing market simulation.

Handles population growth, immigration, emigration, and household formation.
"""

import numpy as np
from typing import Dict, Tuple
from .config import SimulationConfig, MarketState


class PopulationDynamics:
    """
    Models population changes including natural growth and migration.

    Key features:
    - Natural population growth (births and deaths)
    - Immigration and emigration flows
    - Household formation and dissolution
    - Age structure effects (simplified)
    """

    def __init__(self, config: SimulationConfig):
        self.config = config
        self.rng = np.random.default_rng(42)  # Reproducible randomness

        # Immigration multiplier (can be adjusted for scenarios)
        self.immigration_multiplier = 1.0

    def set_immigration_scenario(self, scenario: str):
        """Set immigration scenario from predefined options."""
        if scenario in self.config.immigration_scenarios:
            self.immigration_multiplier = self.config.immigration_scenarios[scenario]
        else:
            raise ValueError(f"Unknown scenario: {scenario}")

    def update(self, state: MarketState) -> MarketState:
        """
        Update population for one timestep.

        Args:
            state: Current market state

        Returns:
            Updated market state
        """
        # Monthly rates
        monthly_birth = self.config.get_monthly_rate(self.config.birth_rate)
        monthly_death = self.config.get_monthly_rate(self.config.death_rate)
        monthly_immigration = self.config.get_monthly_rate(
            self.config.base_immigration_rate * self.immigration_multiplier
        )
        monthly_emigration = self.config.get_monthly_rate(self.config.emigration_rate)

        # Natural population change
        births = state.population * monthly_birth
        deaths = state.population * monthly_death

        # Migration flows
        immigration = state.population * monthly_immigration
        emigration = state.population * monthly_emigration

        # Add some randomness (±20% variability)
        immigration *= self.rng.uniform(0.8, 1.2)
        emigration *= self.rng.uniform(0.8, 1.2)
        births *= self.rng.uniform(0.9, 1.1)
        deaths *= self.rng.uniform(0.9, 1.1)

        # Update populations
        state.population += births - deaths + immigration - emigration
        state.immigrant_population += immigration - (
            emigration * state.immigrant_population / state.population
        )
        state.native_population = state.population - state.immigrant_population

        # Store annual rates for tracking
        annual_factor = 12 / self.config.timestep_months
        state.annual_immigration = immigration * annual_factor
        state.annual_emigration = emigration * annual_factor
        state.net_immigration = (immigration - emigration) * annual_factor

        # Update households
        state.households = self._calculate_households(state)

        return state

    def _calculate_households(self, state: MarketState) -> float:
        """
        Calculate number of households based on population and demographics.

        Accounts for:
        - Average household size
        - Household formation trends
        - Immigration effects (immigrants often form larger households initially)
        """
        # Calculate target households based on population
        # Immigrants tend to have slightly larger household sizes initially,
        # but this is simplified to use average household size
        target_households = state.population / self.config.avg_household_size

        # Smooth adjustment (households don't change instantly)
        # People need time to form/dissolve households
        if state.households > 0:
            adjustment_rate = 0.1  # 10% adjustment per month toward target
            new_households = state.households * (1 - adjustment_rate) + target_households * adjustment_rate
        else:
            new_households = target_households

        return new_households

    def get_housing_demand_pressure(self, state: MarketState) -> float:
        """
        Calculate housing demand pressure from population growth.

        Returns:
            Demand pressure factor (1.0 = neutral, >1.0 = increased pressure)
        """
        # If households > housing stock, there's pressure
        housing_need = state.households
        available_housing = state.total_housing - state.vacant

        if available_housing > 0:
            pressure = housing_need / available_housing
        else:
            pressure = 2.0  # High pressure if no housing

        return max(0.5, min(2.0, pressure))  # Clamp to reasonable range

    def project_population(
        self,
        initial_population: float,
        years: int,
        immigration_multiplier: float = 1.0
    ) -> np.ndarray:
        """
        Project population growth over multiple years.

        Args:
            initial_population: Starting population
            years: Number of years to project
            immigration_multiplier: Factor to adjust immigration

        Returns:
            Array of population values for each year
        """
        population = initial_population
        projection = [population]

        annual_growth = (
            self.config.birth_rate -
            self.config.death_rate +
            self.config.base_immigration_rate * immigration_multiplier -
            self.config.emigration_rate
        )

        for _ in range(years):
            population *= (1 + annual_growth)
            projection.append(population)

        return np.array(projection)

    def calculate_demographic_pressure_index(self, state: MarketState) -> float:
        """
        Calculate a demographic pressure index for the housing market.

        Higher values indicate more pressure from demographic factors.

        Returns:
            Pressure index (0-100 scale)
        """
        # Factors contributing to pressure:
        # 1. Population growth rate
        # 2. Immigration rate
        # 3. Household formation rate
        # 4. Housing shortage

        population_growth = (state.population / self.config.initial_population - 1) * 100
        immigration_pressure = (state.net_immigration / state.population) * 1000
        household_pressure = (state.households / (state.total_housing * 0.97) - 1) * 100

        # Weighted combination
        pressure_index = (
            population_growth * 0.2 +
            immigration_pressure * 0.4 +
            household_pressure * 0.4
        )

        return max(0, min(100, pressure_index))
