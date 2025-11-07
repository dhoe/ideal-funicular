"""
Configuration parameters for the Dutch housing market simulation.

Based on real Dutch housing market data and economic indicators.
"""

from dataclasses import dataclass
from typing import Dict, List
import numpy as np


@dataclass
class SimulationConfig:
    """Main configuration for the housing market simulation."""

    # Simulation parameters
    start_year: int = 2020
    end_year: int = 2050
    timestep_months: int = 1  # Monthly timesteps

    # Initial conditions (based on Dutch statistics)
    initial_population: int = 17_500_000  # Netherlands population
    initial_housing_stock: int = 8_000_000  # Total dwellings
    initial_avg_price: float = 350_000  # Average house price in euros

    # Population dynamics
    birth_rate: float = 0.0095  # Annual births per capita
    death_rate: float = 0.0090  # Annual deaths per capita
    base_immigration_rate: float = 0.0040  # Annual net immigration rate (baseline)
    emigration_rate: float = 0.0015  # Annual emigration rate

    # Household formation
    avg_household_size: float = 2.19  # Average persons per household (17.5M / 8M)
    household_formation_age: int = 25  # Average age of household formation
    household_dissolution_rate: float = 0.015  # Annual rate

    # Housing supply
    annual_construction_rate: float = 0.012  # As fraction of existing stock
    construction_delay_months: int = 24  # Time from planning to completion
    demolition_rate: float = 0.002  # Annual demolition/removal rate

    # Housing market segments (percentages)
    owner_occupied_share: float = 0.57  # Owner-occupied housing
    private_rental_share: float = 0.18  # Private rental
    social_rental_share: float = 0.25  # Social/affordable housing

    # Economic parameters
    base_gdp_growth: float = 0.02  # Annual GDP growth rate
    base_interest_rate: float = 0.025  # Mortgage interest rate
    income_growth_rate: float = 0.015  # Annual income growth
    median_income: float = 38_000  # Median annual income in euros

    # Price dynamics
    price_elasticity_supply: float = 0.3  # Supply response to price
    price_elasticity_demand: float = -0.7  # Demand response to price
    adjustment_speed: float = 0.05  # Price adjustment speed (0-1), slower = more stable

    # Regional distribution (simplified)
    regions: List[str] = None
    regional_weights: Dict[str, float] = None

    # Immigration scenarios
    immigration_scenarios: Dict[str, float] = None

    def __post_init__(self):
        """Initialize derived parameters."""
        if self.regions is None:
            self.regions = [
                'Randstad',  # Amsterdam, Rotterdam, Den Haag, Utrecht area
                'North',     # Northern provinces
                'East',      # Eastern provinces
                'South'      # Southern provinces
            ]

        if self.regional_weights is None:
            # Population distribution across regions
            self.regional_weights = {
                'Randstad': 0.45,  # Highly urbanized, most attractive
                'North': 0.15,
                'East': 0.20,
                'South': 0.20
            }

        if self.immigration_scenarios is None:
            # Different immigration scenarios as multipliers of base rate
            self.immigration_scenarios = {
                'low': 0.5,      # 50% of baseline
                'baseline': 1.0,  # Current rate
                'high': 1.5,      # 50% increase
                'very_high': 2.0, # Doubled immigration
                'crisis': 3.0     # Crisis scenario (e.g., large refugee influx)
            }

    @property
    def total_timesteps(self) -> int:
        """Calculate total number of simulation timesteps."""
        years = self.end_year - self.start_year
        return years * 12 // self.timestep_months

    @property
    def timesteps_per_year(self) -> int:
        """Number of timesteps per year."""
        return 12 // self.timestep_months

    def get_monthly_rate(self, annual_rate: float) -> float:
        """Convert annual rate to monthly rate."""
        return (1 + annual_rate) ** (1/12) - 1


@dataclass
class MarketState:
    """Current state of the housing market."""

    timestep: int = 0
    year: float = 2020.0

    # Population
    population: float = 17_500_000
    native_population: float = 15_000_000
    immigrant_population: float = 2_500_000
    households: float = 8_000_000

    # Housing stock
    total_housing: int = 8_000_000
    owner_occupied: int = 4_560_000
    private_rental: int = 1_440_000
    social_rental: int = 2_000_000
    vacant: int = 200_000
    under_construction: int = 50_000

    # Prices
    avg_price: float = 350_000
    price_index: float = 100.0  # Baseline = 100
    regional_prices: Dict[str, float] = None

    # Market dynamics
    demand: float = 0
    supply: float = 0
    shortage: float = 0  # Negative = surplus

    # Economic indicators
    gdp_index: float = 100.0
    interest_rate: float = 0.025
    median_income: float = 38_000
    affordability_ratio: float = 9.2  # Price to income ratio

    # Immigration
    annual_immigration: float = 70_000
    annual_emigration: float = 26_250
    net_immigration: float = 43_750

    def __post_init__(self):
        """Initialize regional prices if not set."""
        if self.regional_prices is None:
            self.regional_prices = {
                'Randstad': self.avg_price * 1.25,  # 25% above average
                'North': self.avg_price * 0.75,      # 25% below average
                'East': self.avg_price * 0.85,       # 15% below average
                'South': self.avg_price * 0.95       # 5% below average
            }

    @property
    def occupancy_rate(self) -> float:
        """Calculate housing occupancy rate."""
        occupied = self.total_housing - self.vacant
        return occupied / self.total_housing if self.total_housing > 0 else 0

    @property
    def housing_shortage_pct(self) -> float:
        """Housing shortage as percentage of demand."""
        return (self.shortage / self.households * 100) if self.households > 0 else 0
