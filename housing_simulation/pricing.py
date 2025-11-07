"""
Housing price mechanism module for the housing market simulation.

Models price discovery, market equilibrium, and affordability.
"""

import numpy as np
from typing import Dict, Tuple
from .config import SimulationConfig, MarketState


class PriceMechanism:
    """
    Models housing price dynamics and market equilibrium.

    Key features:
    - Supply-demand equilibrium pricing
    - Regional price differentiation
    - Speculative dynamics
    - Affordability constraints
    - Interest rate effects
    """

    def __init__(self, config: SimulationConfig):
        self.config = config
        self.rng = np.random.default_rng(44)

        # Price momentum and memory
        self.price_momentum = 0.0
        self.recent_price_changes = []

    def update(self, state: MarketState) -> MarketState:
        """
        Update housing prices for one timestep.

        Args:
            state: Current market state

        Returns:
            Updated market state with new prices
        """
        # Calculate supply and demand
        supply = self._calculate_effective_supply(state)
        demand = self._calculate_effective_demand(state)

        state.supply = supply
        state.demand = demand
        state.shortage = demand - supply

        # Calculate price change based on supply-demand imbalance
        price_change_rate = self._calculate_price_change(state, supply, demand)

        # Update prices
        state.avg_price *= (1 + price_change_rate)

        # Update price index
        state.price_index = (state.avg_price / self.config.initial_avg_price) * 100

        # Update regional prices
        state.regional_prices = self._update_regional_prices(state)

        # Update affordability
        state.affordability_ratio = state.avg_price / state.median_income

        # Track price momentum
        self.recent_price_changes.append(price_change_rate)
        if len(self.recent_price_changes) > 12:
            self.recent_price_changes.pop(0)
        self.price_momentum = np.mean(self.recent_price_changes)

        return state

    def _calculate_effective_supply(self, state: MarketState) -> float:
        """
        Calculate effective housing supply available to the market.

        Not all housing stock is equally available (some is social housing,
        some is occupied and not for sale).
        """
        # Occupied housing (not immediately available)
        occupied = state.total_housing - state.vacant

        # Only a fraction of occupied housing comes to market each period
        # Dutch market: about 5-6% annual turnover
        annual_turnover = 0.055
        monthly_turnover = annual_turnover / (12 / self.config.timestep_months)

        # Effective supply = turnover from occupied + new completions
        effective_supply = occupied * monthly_turnover

        # Vacant units are already counted in the above (owners list them when vacant)
        # So we don't double-count

        return effective_supply

    def _calculate_effective_demand(self, state: MarketState) -> float:
        """
        Calculate effective housing demand.

        Demand depends on:
        - Household formation
        - Income and affordability
        - Interest rates
        - Expectations
        """
        # Base demand: households looking to buy/rent in this period
        # Use turnover rate as base (people moving, young people forming households, etc.)
        # Should match supply turnover rate in equilibrium
        annual_turnover_rate = 0.055  # 5.5% of households move per year (matches supply)
        monthly_rate = annual_turnover_rate / (12 / self.config.timestep_months)
        base_demand = state.households * monthly_rate

        # If there's a shortage, add pressure (more people looking)
        housing_per_household = state.total_housing / state.households if state.households > 0 else 1.0
        target_ratio = 1.03  # Healthy market with 3% vacancy

        if housing_per_household < target_ratio:
            shortage_pressure = (target_ratio - housing_per_household) / target_ratio
            base_demand *= (1 + shortage_pressure * 0.5)  # Up to 50% more searchers

        # Affordability constraint: if prices too high relative to income, demand is constrained
        affordability_factor = self._calculate_affordability_factor(state)

        # Interest rate effect: lower rates increase demand
        interest_effect = 1 - (state.interest_rate - self.config.base_interest_rate) * 3
        interest_effect = max(0.5, min(1.5, interest_effect))

        # Expectation effect: if prices rising, people rush in (but limit impact)
        expectation_factor = 1 + np.clip(self.price_momentum * 2, -0.3, 0.3)

        # Combine factors
        effective_demand = (
            base_demand *
            affordability_factor *
            interest_effect *
            expectation_factor
        )

        return max(0, effective_demand)

    def _calculate_affordability_factor(self, state: MarketState) -> float:
        """
        Calculate how affordability constrains demand.

        Returns factor between 0 and 1.5 where:
        - 1.0 = normal affordability
        - <1.0 = constrained by high prices
        - >1.0 = boosted by low prices
        """
        # Calculate mortgage payment as fraction of income
        # Simplified: assume 30-year mortgage
        monthly_rate = state.interest_rate / 12
        n_payments = 30 * 12

        if monthly_rate > 0:
            monthly_payment = (
                state.avg_price *
                monthly_rate *
                (1 + monthly_rate) ** n_payments /
                ((1 + monthly_rate) ** n_payments - 1)
            )
        else:
            monthly_payment = state.avg_price / n_payments

        monthly_income = state.median_income / 12

        # Typical lending standard: payment should be < 30% of income
        payment_ratio = monthly_payment / monthly_income if monthly_income > 0 else 10

        # Affordability factor: decreases as payment ratio increases
        if payment_ratio < 0.25:
            factor = 1.2  # Very affordable, increased demand
        elif payment_ratio < 0.35:
            factor = 1.0  # Normal
        elif payment_ratio < 0.50:
            factor = 0.7  # Challenging
        else:
            factor = 0.4  # Very difficult

        return factor

    def _calculate_price_change(
        self,
        state: MarketState,
        supply: float,
        demand: float
    ) -> float:
        """
        Calculate monthly price change rate based on supply-demand imbalance.

        Args:
            state: Current market state
            supply: Effective supply
            demand: Effective demand

        Returns:
            Monthly price change rate (e.g., 0.01 = 1% increase)
        """
        if supply <= 0:
            # Extreme shortage
            return 0.05  # 5% monthly increase (capped)

        # Imbalance ratio
        imbalance = (demand - supply) / supply

        # Price response to imbalance
        # Uses elasticity and adjustment speed
        price_change = (
            imbalance *
            abs(self.config.price_elasticity_demand) *
            self.config.adjustment_speed
        )

        # Add momentum (prices tend to continue in same direction)
        momentum_effect = self.price_momentum * 0.3
        price_change += momentum_effect

        # Market noise
        noise = self.rng.normal(0, 0.002)  # ±0.2% random noise
        price_change += noise

        # Constraints: prevent extreme changes
        monthly_max_change = 0.03  # 3% per month maximum
        price_change = max(-monthly_max_change, min(monthly_max_change, price_change))

        # Prices are sticky downward (harder to fall than to rise)
        if price_change < 0:
            price_change *= 0.5  # Downward adjustment is slower

        return price_change

    def _update_regional_prices(self, state: MarketState) -> Dict[str, float]:
        """
        Update regional price variations.

        Some regions (Randstad) are more attractive and have higher price growth.
        """
        regional_prices = {}

        for region, weight in self.config.regional_weights.items():
            current_price = state.regional_prices[region]

            # Base regional multiplier
            if region == 'Randstad':
                multiplier = 1.2  # More attractive, prices rise faster
            elif region == 'South':
                multiplier = 1.05
            else:
                multiplier = 0.95  # Less attractive, slower growth

            # Regional price changes track national price but with regional factors
            national_change = (state.avg_price / self.config.initial_avg_price)
            regional_change = national_change ** multiplier

            new_price = self.config.initial_avg_price * regional_change

            # Adjust relative to region's baseline
            baseline_regional = self.config.initial_avg_price * (current_price / state.avg_price)
            regional_prices[region] = 0.9 * current_price + 0.1 * new_price

        return regional_prices

    def calculate_price_to_income_ratio(self, state: MarketState) -> float:
        """Calculate the price-to-income ratio (affordability metric)."""
        return state.avg_price / state.median_income if state.median_income > 0 else 0

    def calculate_housing_cost_burden(self, state: MarketState) -> float:
        """
        Calculate housing cost burden as percentage of income.

        Returns:
            Percentage of median income spent on housing
        """
        # Assume 30-year mortgage
        monthly_rate = state.interest_rate / 12
        n_payments = 30 * 12

        if monthly_rate > 0:
            monthly_payment = (
                state.avg_price *
                monthly_rate *
                (1 + monthly_rate) ** n_payments /
                ((1 + monthly_rate) ** n_payments - 1)
            )
        else:
            monthly_payment = state.avg_price / n_payments

        monthly_income = state.median_income / 12

        burden_pct = (monthly_payment / monthly_income * 100) if monthly_income > 0 else 100

        return burden_pct

    def get_market_temperature(self, state: MarketState) -> str:
        """
        Get qualitative assessment of market conditions.

        Returns:
            Market temperature: "Cold", "Cool", "Normal", "Warm", "Hot"
        """
        # Based on price momentum and shortage
        if self.price_momentum > 0.02 or state.housing_shortage_pct > 10:
            return "Hot"
        elif self.price_momentum > 0.01 or state.housing_shortage_pct > 5:
            return "Warm"
        elif self.price_momentum < -0.01 or state.housing_shortage_pct < -5:
            return "Cool"
        elif self.price_momentum < -0.02:
            return "Cold"
        else:
            return "Normal"
