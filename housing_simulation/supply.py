"""
Housing supply module for the housing market simulation.

Manages housing construction, demolition, and stock dynamics.
"""

import numpy as np
from collections import deque
from typing import Deque, Dict
from .config import SimulationConfig, MarketState


class HousingSupply:
    """
    Models housing supply dynamics including construction and demolition.

    Key features:
    - Construction with realistic time delays
    - Price-responsive construction rates
    - Demolition and renovation
    - Different housing types (owner-occupied, rental, social)
    - Regional supply differences
    """

    def __init__(self, config: SimulationConfig):
        self.config = config
        self.rng = np.random.default_rng(43)

        # Construction pipeline: queue of projects with completion times
        self.construction_pipeline: Deque[int] = deque()

        # Initialize pipeline with some ongoing projects
        self._initialize_pipeline()

        # Construction response parameters
        self.construction_multiplier = 1.0  # Can be adjusted for policy scenarios

    def _initialize_pipeline(self):
        """Initialize construction pipeline with ongoing projects."""
        delay_steps = self.config.construction_delay_months // self.config.timestep_months

        # Distribute initial under-construction units across the pipeline
        units_per_month = self.config.initial_housing_stock * self.config.annual_construction_rate / 12

        for i in range(delay_steps):
            self.construction_pipeline.append(int(units_per_month))

    def update(self, state: MarketState) -> MarketState:
        """
        Update housing supply for one timestep.

        Args:
            state: Current market state

        Returns:
            Updated market state
        """
        # Complete projects from pipeline
        completed_units = self._complete_construction()
        state.total_housing += completed_units

        # Start new construction
        new_construction = self._calculate_new_construction(state)
        self._start_construction(new_construction)

        # Demolition and removal
        demolished_units = self._calculate_demolition(state)
        state.total_housing -= demolished_units

        # Update under_construction count
        state.under_construction = sum(self.construction_pipeline)

        # Update housing by type
        state = self._update_housing_types(state, completed_units)

        # Update vacancy
        state.vacant = self._calculate_vacancy(state)

        return state

    def _complete_construction(self) -> int:
        """Complete construction projects that have reached the end of pipeline."""
        if self.construction_pipeline:
            return self.construction_pipeline.popleft()
        return 0

    def _calculate_new_construction(self, state: MarketState) -> int:
        """
        Calculate new construction starts based on market conditions.

        Construction responds to:
        - Housing shortage
        - Price levels
        - Profitability
        - Policy constraints
        """
        # Base construction rate
        base_construction = (
            state.total_housing *
            self.config.annual_construction_rate *
            self.construction_multiplier /
            (12 / self.config.timestep_months)
        )

        # Price factor: higher prices incentivize more construction
        price_ratio = state.avg_price / self.config.initial_avg_price
        price_factor = 1 + (price_ratio - 1) * self.config.price_elasticity_supply

        # Shortage factor: shortages drive construction
        shortage_factor = 1.0
        if state.households > 0:
            housing_per_household = state.total_housing / state.households
            target_ratio = 1.03  # Target 3% vacancy for healthy market

            if housing_per_household < target_ratio:
                shortage_intensity = (target_ratio - housing_per_household) / target_ratio
                shortage_factor = 1 + shortage_intensity * 0.5  # Up to 50% boost

        # Economic cycle factor
        gdp_factor = state.gdp_index / 100

        # Interest rate factor: higher rates reduce construction
        interest_factor = 1 - (state.interest_rate - self.config.base_interest_rate) * 5

        # Combine factors
        construction = base_construction * price_factor * shortage_factor * gdp_factor * interest_factor

        # Add variability
        construction *= self.rng.uniform(0.85, 1.15)

        # Apply constraints (can't be negative, realistic maximum)
        max_construction = base_construction * 2.5  # Can't increase more than 2.5x
        construction = max(0, min(construction, max_construction))

        return int(construction)

    def _start_construction(self, units: int):
        """Add new construction to the pipeline."""
        self.construction_pipeline.append(units)

    def _calculate_demolition(self, state: MarketState) -> int:
        """
        Calculate housing demolition/removal.

        Accounts for:
        - Age and depreciation
        - Urban renewal projects
        - Natural disasters (rare events)
        """
        # Base demolition rate
        base_demolition = (
            state.total_housing *
            self.config.demolition_rate /
            (12 / self.config.timestep_months)
        )

        # Higher prices may slow demolition (renovation instead)
        price_ratio = state.avg_price / self.config.initial_avg_price
        price_factor = 1 / (1 + (price_ratio - 1) * 0.3)

        demolition = base_demolition * price_factor

        # Add small random variability
        demolition *= self.rng.uniform(0.9, 1.1)

        # Rare events (0.5% chance of larger demolition)
        if self.rng.random() < 0.005:
            demolition *= 1.5

        return int(demolition)

    def _update_housing_types(self, state: MarketState, new_units: int) -> MarketState:
        """
        Update housing by type (owner-occupied, rental, social).

        New construction is distributed according to policy targets.
        """
        # Distribute new units
        new_owner = int(new_units * self.config.owner_occupied_share)
        new_private_rental = int(new_units * self.config.private_rental_share)
        new_social = new_units - new_owner - new_private_rental

        state.owner_occupied += new_owner
        state.private_rental += new_private_rental
        state.social_rental += new_social

        # Maintain approximate ratios
        total = state.owner_occupied + state.private_rental + state.social_rental

        if total != state.total_housing:
            diff = state.total_housing - total
            # Distribute difference to owner-occupied
            state.owner_occupied += diff

        return state

    def _calculate_vacancy(self, state: MarketState) -> int:
        """
        Calculate vacant housing units.

        Vacancy depends on:
        - Market tightness
        - Frictional vacancy (units between occupants)
        - Seasonal factors
        """
        # Target vacancy rate for healthy market
        base_vacancy_rate = 0.03  # 3%

        # Adjust based on market conditions
        housing_per_household = state.total_housing / state.households if state.households > 0 else 1.0

        if housing_per_household > 1.03:
            # Surplus: higher vacancy
            vacancy_rate = base_vacancy_rate + (housing_per_household - 1.03) * 0.5
        else:
            # Shortage: lower vacancy
            vacancy_rate = base_vacancy_rate * housing_per_household / 1.03

        vacancy_rate = max(0.01, min(0.10, vacancy_rate))  # Between 1% and 10%

        vacant_units = int(state.total_housing * vacancy_rate)

        return vacant_units

    def set_construction_policy(self, multiplier: float):
        """
        Adjust construction rate through policy (e.g., zoning, subsidies).

        Args:
            multiplier: Factor to adjust construction (1.0 = baseline)
        """
        self.construction_multiplier = max(0.5, min(2.0, multiplier))

    def get_supply_elasticity(self, state: MarketState) -> float:
        """
        Calculate current supply elasticity.

        Returns:
            Elasticity measure (higher = more responsive supply)
        """
        # Factors that affect supply elasticity:
        # - Available land (decreases over time)
        # - Regulatory environment
        # - Construction capacity

        # Simplified: decreases as total stock grows
        land_constraint = 1 - (state.total_housing / (self.config.initial_housing_stock * 1.5))
        land_constraint = max(0.3, land_constraint)  # Minimum elasticity

        elasticity = self.config.price_elasticity_supply * land_constraint * self.construction_multiplier

        return elasticity
