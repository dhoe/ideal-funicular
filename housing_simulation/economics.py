"""
Economic factors module for the housing market simulation.

Models macroeconomic conditions affecting the housing market.
"""

import numpy as np
from .config import SimulationConfig, MarketState


class Economics:
    """
    Models macroeconomic factors influencing the housing market.

    Key features:
    - GDP growth cycles
    - Interest rate dynamics
    - Income growth
    - Economic shocks
    """

    def __init__(self, config: SimulationConfig):
        self.config = config
        self.rng = np.random.default_rng(45)

        # Economic cycle parameters
        self.cycle_phase = 0  # Radians in economic cycle
        self.cycle_period = 120  # Months (10-year cycle)

        # Shock probability and state
        self.in_shock = False
        self.shock_duration = 0

    def update(self, state: MarketState) -> MarketState:
        """
        Update economic conditions for one timestep.

        Args:
            state: Current market state

        Returns:
            Updated market state
        """
        # Update GDP
        state.gdp_index = self._calculate_gdp_index(state)

        # Update interest rates
        state.interest_rate = self._calculate_interest_rate(state)

        # Update median income
        state.median_income = self._calculate_median_income(state)

        # Advance cycle
        self.cycle_phase += 2 * np.pi / self.cycle_period

        return state

    def _calculate_gdp_index(self, state: MarketState) -> float:
        """
        Calculate GDP index with cyclical variation.

        Includes:
        - Base growth trend
        - Cyclical component
        - Random shocks
        """
        # Base growth
        months_elapsed = state.timestep * self.config.timestep_months
        years_elapsed = months_elapsed / 12
        trend_growth = (1 + self.config.base_gdp_growth) ** years_elapsed

        # Cyclical component (business cycle)
        cycle_amplitude = 0.15  # ±15% variation
        cycle_component = 1 + cycle_amplitude * np.sin(self.cycle_phase)

        # Economic shocks
        shock_component = self._handle_economic_shocks()

        # Combine
        gdp_index = 100 * trend_growth * cycle_component * shock_component

        return gdp_index

    def _calculate_interest_rate(self, state: MarketState) -> float:
        """
        Calculate interest rate based on economic conditions.

        Interest rates respond to:
        - GDP growth (Taylor rule approximation)
        - Inflation (proxied by house price growth)
        - Central bank policy
        """
        # Base rate
        base_rate = self.config.base_interest_rate

        # GDP component: higher growth → higher rates
        gdp_factor = (state.gdp_index / 100 - 1) * 0.5

        # Inflation component: use house price growth as proxy
        # (real inflation would include other goods)
        price_growth_annual = ((state.avg_price / self.config.initial_avg_price) ** (12 / max(1, state.timestep)) - 1)
        inflation_factor = max(0, price_growth_annual - 0.02) * 0.3  # Target 2% inflation

        # Cyclical policy
        cycle_factor = -0.01 * np.sin(self.cycle_phase)  # Counter-cyclical

        # Combine
        interest_rate = base_rate + gdp_factor + inflation_factor + cycle_factor

        # Add some randomness
        interest_rate += self.rng.normal(0, 0.001)

        # Constraints: rates don't go too extreme
        interest_rate = max(0.001, min(0.10, interest_rate))  # Between 0.1% and 10%

        # Smooth changes (central banks don't change rates drastically)
        if state.timestep > 0:
            max_change = 0.002  # 0.2% maximum change per month
            change = interest_rate - state.interest_rate
            change = max(-max_change, min(max_change, change))
            interest_rate = state.interest_rate + change

        return interest_rate

    def _calculate_median_income(self, state: MarketState) -> float:
        """
        Calculate median income based on economic growth.

        Income growth tracks GDP with some lag.
        """
        # Base income growth
        months_elapsed = state.timestep * self.config.timestep_months
        years_elapsed = months_elapsed / 12

        base_income = self.config.median_income
        income_growth = (1 + self.config.income_growth_rate) ** years_elapsed

        # GDP effect (income grows with GDP but not 1:1)
        gdp_effect = (state.gdp_index / 100) ** 0.7

        # Combine
        median_income = base_income * income_growth * gdp_effect

        # Add small random variation
        median_income *= self.rng.uniform(0.98, 1.02)

        return median_income

    def _handle_economic_shocks(self) -> float:
        """
        Model economic shocks (recessions, crises).

        Returns:
            Multiplier for GDP (1.0 = no shock, <1.0 = negative shock)
        """
        if self.in_shock:
            # In shock period
            self.shock_duration -= 1
            if self.shock_duration <= 0:
                self.in_shock = False
                return 0.95  # Recovery starts
            else:
                return 0.85  # Recession effect
        else:
            # Check for new shock (1% chance per month of recession)
            if self.rng.random() < 0.01:
                self.in_shock = True
                self.shock_duration = self.rng.integers(6, 18)  # 6-18 month recession
                return 0.90  # Initial shock
            else:
                return 1.0  # No shock

    def trigger_shock(self, severity: float = 0.15, duration_months: int = 12):
        """
        Manually trigger an economic shock (for scenario testing).

        Args:
            severity: How much GDP drops (0.15 = 15% drop)
            duration_months: How long the shock lasts
        """
        self.in_shock = True
        self.shock_duration = duration_months
        self.shock_severity = severity
