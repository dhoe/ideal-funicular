"""
Visualization tools for the housing market simulation.

Creates charts and plots to analyze simulation results.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from typing import Dict, List, Optional
import seaborn as sns


# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (14, 10)
plt.rcParams['font.size'] = 10


class Visualizer:
    """
    Creates visualizations for housing market simulation results.
    """

    def __init__(self):
        self.colors = {
            'low': '#2ecc71',
            'baseline': '#3498db',
            'high': '#f39c12',
            'very_high': '#e74c3c',
            'crisis': '#9b59b6'
        }

    def plot_simulation_overview(
        self,
        df: pd.DataFrame,
        scenario: str = "baseline",
        save_path: Optional[str] = None
    ):
        """
        Create comprehensive overview plot of a single simulation.

        Args:
            df: Simulation history DataFrame
            scenario: Scenario name for title
            save_path: Path to save figure (if provided)
        """
        fig = plt.figure(figsize=(16, 12))
        gs = gridspec.GridSpec(3, 2, figure=fig, hspace=0.3, wspace=0.3)

        # 1. House prices over time
        ax1 = fig.add_subplot(gs[0, 0])
        ax1.plot(df['year'], df['avg_price'] / 1000, linewidth=2, color='#3498db')
        ax1.set_xlabel('Year')
        ax1.set_ylabel('Average Price (€1000s)')
        ax1.set_title('House Prices Over Time')
        ax1.grid(True, alpha=0.3)

        # 2. Population growth
        ax2 = fig.add_subplot(gs[0, 1])
        ax2.plot(df['year'], df['population'] / 1_000_000, linewidth=2, color='#e74c3c', label='Total')
        ax2.plot(df['year'], df['immigrant_population'] / 1_000_000, linewidth=2, color='#f39c12', label='Immigrant')
        ax2.set_xlabel('Year')
        ax2.set_ylabel('Population (Millions)')
        ax2.set_title('Population Growth')
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        # 3. Housing stock and shortage
        ax3 = fig.add_subplot(gs[1, 0])
        ax3.plot(df['year'], df['total_housing'] / 1000, linewidth=2, color='#2ecc71', label='Total Stock')
        ax3.plot(df['year'], df['households'] / 1000, linewidth=2, color='#9b59b6', label='Households')
        ax3.set_xlabel('Year')
        ax3.set_ylabel('Units (Thousands)')
        ax3.set_title('Housing Stock vs Households')
        ax3.legend()
        ax3.grid(True, alpha=0.3)

        # 4. Affordability
        ax4 = fig.add_subplot(gs[1, 1])
        ax4.plot(df['year'], df['affordability_ratio'], linewidth=2, color='#e67e22')
        ax4.axhline(y=9.2, color='gray', linestyle='--', alpha=0.5, label='Initial')
        ax4.set_xlabel('Year')
        ax4.set_ylabel('Price-to-Income Ratio')
        ax4.set_title('Housing Affordability')
        ax4.legend()
        ax4.grid(True, alpha=0.3)

        # 5. Supply and demand
        ax5 = fig.add_subplot(gs[2, 0])
        ax5.plot(df['year'], df['demand'], linewidth=2, color='#e74c3c', label='Demand')
        ax5.plot(df['year'], df['supply'], linewidth=2, color='#2ecc71', label='Supply')
        ax5.set_xlabel('Year')
        ax5.set_ylabel('Units per Period')
        ax5.set_title('Housing Supply and Demand')
        ax5.legend()
        ax5.grid(True, alpha=0.3)

        # 6. Economic indicators
        ax6 = fig.add_subplot(gs[2, 1])
        ax6_twin = ax6.twinx()
        ax6.plot(df['year'], df['gdp_index'], linewidth=2, color='#3498db', label='GDP Index')
        ax6_twin.plot(df['year'], df['interest_rate'] * 100, linewidth=2, color='#e74c3c', label='Interest Rate')
        ax6.set_xlabel('Year')
        ax6.set_ylabel('GDP Index', color='#3498db')
        ax6_twin.set_ylabel('Interest Rate (%)', color='#e74c3c')
        ax6.set_title('Economic Conditions')
        ax6.tick_params(axis='y', labelcolor='#3498db')
        ax6_twin.tick_params(axis='y', labelcolor='#e74c3c')
        ax6.grid(True, alpha=0.3)

        fig.suptitle(f'Dutch Housing Market Simulation - {scenario.upper()} Scenario', fontsize=16, fontweight='bold')

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Saved plot to {save_path}")

        plt.tight_layout()
        return fig

    def plot_scenario_comparison(
        self,
        results: Dict[str, pd.DataFrame],
        save_path: Optional[str] = None
    ):
        """
        Compare multiple immigration scenarios.

        Args:
            results: Dictionary mapping scenario names to DataFrames
            save_path: Path to save figure (if provided)
        """
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))

        scenarios = list(results.keys())

        # 1. Price comparison
        ax1 = axes[0, 0]
        for scenario in scenarios:
            df = results[scenario]
            color = self.colors.get(scenario, '#95a5a6')
            ax1.plot(df['year'], df['avg_price'] / 1000, linewidth=2.5, label=scenario.capitalize(), color=color)
        ax1.set_xlabel('Year')
        ax1.set_ylabel('Average Price (€1000s)')
        ax1.set_title('House Prices by Immigration Scenario', fontsize=12, fontweight='bold')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # 2. Population comparison
        ax2 = axes[0, 1]
        for scenario in scenarios:
            df = results[scenario]
            color = self.colors.get(scenario, '#95a5a6')
            ax2.plot(df['year'], df['population'] / 1_000_000, linewidth=2.5, label=scenario.capitalize(), color=color)
        ax2.set_xlabel('Year')
        ax2.set_ylabel('Population (Millions)')
        ax2.set_title('Population Growth by Scenario', fontsize=12, fontweight='bold')
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        # 3. Housing shortage comparison
        ax3 = axes[1, 0]
        for scenario in scenarios:
            df = results[scenario]
            color = self.colors.get(scenario, '#95a5a6')
            ax3.plot(df['year'], df['housing_shortage_pct'], linewidth=2.5, label=scenario.capitalize(), color=color)
        ax3.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
        ax3.set_xlabel('Year')
        ax3.set_ylabel('Housing Shortage (%)')
        ax3.set_title('Housing Shortage by Scenario', fontsize=12, fontweight='bold')
        ax3.legend()
        ax3.grid(True, alpha=0.3)

        # 4. Affordability comparison
        ax4 = axes[1, 1]
        for scenario in scenarios:
            df = results[scenario]
            color = self.colors.get(scenario, '#95a5a6')
            ax4.plot(df['year'], df['affordability_ratio'], linewidth=2.5, label=scenario.capitalize(), color=color)
        ax4.set_xlabel('Year')
        ax4.set_ylabel('Price-to-Income Ratio')
        ax4.set_title('Affordability by Scenario', fontsize=12, fontweight='bold')
        ax4.legend()
        ax4.grid(True, alpha=0.3)

        fig.suptitle('Immigration Impact on Dutch Housing Market', fontsize=16, fontweight='bold')

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Saved comparison plot to {save_path}")

        plt.tight_layout()
        return fig

    def plot_immigration_impact_analysis(
        self,
        comparison_df: pd.DataFrame,
        save_path: Optional[str] = None
    ):
        """
        Create detailed analysis of immigration impact.

        Args:
            comparison_df: DataFrame from analyze_immigration_impact()
            save_path: Path to save figure (if provided)
        """
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))

        scenarios = comparison_df['scenario'].values
        colors = [self.colors.get(s, '#95a5a6') for s in scenarios]

        # 1. Final prices by scenario
        ax1 = axes[0, 0]
        bars1 = ax1.bar(scenarios, comparison_df['final_price'] / 1000, color=colors, alpha=0.7)
        ax1.set_ylabel('Final Price (€1000s)')
        ax1.set_title('Final House Prices by Scenario', fontweight='bold')
        ax1.tick_params(axis='x', rotation=45)

        # Add value labels
        for bar in bars1:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'€{height:.0f}k', ha='center', va='bottom')

        # 2. Price change from baseline
        ax2 = axes[0, 1]
        bars2 = ax2.bar(scenarios, comparison_df['price_diff_pct'], color=colors, alpha=0.7)
        ax2.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
        ax2.set_ylabel('Price Difference from Baseline (%)')
        ax2.set_title('Impact on Prices Relative to Baseline', fontweight='bold')
        ax2.tick_params(axis='x', rotation=45)

        # Add value labels
        for bar in bars2:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:+.1f}%', ha='center', va='bottom' if height > 0 else 'top')

        # 3. Population change
        ax3 = axes[1, 0]
        bars3 = ax3.bar(scenarios, comparison_df['population_change_pct'], color=colors, alpha=0.7)
        ax3.set_ylabel('Population Change (%)')
        ax3.set_title('Population Growth by Scenario', fontweight='bold')
        ax3.tick_params(axis='x', rotation=45)

        # Add value labels
        for bar in bars3:
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:+.1f}%', ha='center', va='bottom')

        # 4. Affordability
        ax4 = axes[1, 1]
        bars4 = ax4.bar(scenarios, comparison_df['affordability_ratio'], color=colors, alpha=0.7)
        ax4.axhline(y=9.2, color='gray', linestyle='--', alpha=0.5, label='Initial')
        ax4.set_ylabel('Price-to-Income Ratio')
        ax4.set_title('Final Affordability by Scenario', fontweight='bold')
        ax4.tick_params(axis='x', rotation=45)
        ax4.legend()

        # Add value labels
        for bar in bars4:
            height = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}x', ha='center', va='bottom')

        fig.suptitle('Immigration Impact Analysis', fontsize=16, fontweight='bold')

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Saved impact analysis to {save_path}")

        plt.tight_layout()
        return fig

    def create_summary_table(self, results: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """
        Create summary statistics table for multiple scenarios.

        Args:
            results: Dictionary mapping scenario names to DataFrames

        Returns:
            Summary DataFrame
        """
        summary_data = []

        for scenario, df in results.items():
            initial = df.iloc[0]
            final = df.iloc[-1]

            summary_data.append({
                'Scenario': scenario.capitalize(),
                'Final Price (€)': f"€{final['avg_price']:,.0f}",
                'Price Change (%)': f"{(final['avg_price'] - initial['avg_price']) / initial['avg_price'] * 100:+.1f}%",
                'Final Population': f"{final['population']:,.0f}",
                'Population Change (%)': f"{(final['population'] - initial['population']) / initial['population'] * 100:+.1f}%",
                'Housing Shortage': f"{final['shortage']:,.0f}",
                'Affordability (P/I)': f"{final['affordability_ratio']:.1f}x",
            })

        return pd.DataFrame(summary_data)

    def plot_price_heatmap(
        self,
        results: Dict[str, pd.DataFrame],
        save_path: Optional[str] = None
    ):
        """
        Create heatmap showing price evolution across scenarios.

        Args:
            results: Dictionary mapping scenario names to DataFrames
            save_path: Path to save figure (if provided)
        """
        # Prepare data for heatmap
        scenarios = list(results.keys())
        years = results[scenarios[0]]['year'].values

        # Sample every 12 months for readability
        sample_indices = range(0, len(years), 12)
        years_sampled = years[sample_indices]

        # Create matrix of price indices
        price_matrix = []
        for scenario in scenarios:
            df = results[scenario]
            prices = df['price_index'].values[sample_indices]
            price_matrix.append(prices)

        price_matrix = np.array(price_matrix)

        # Create heatmap
        fig, ax = plt.subplots(figsize=(14, 6))
        im = ax.imshow(price_matrix, aspect='auto', cmap='RdYlGn_r', interpolation='bilinear')

        # Set ticks and labels
        ax.set_xticks(range(len(years_sampled)))
        ax.set_xticklabels([f"{y:.0f}" for y in years_sampled], rotation=45)
        ax.set_yticks(range(len(scenarios)))
        ax.set_yticklabels([s.capitalize() for s in scenarios])

        ax.set_xlabel('Year')
        ax.set_ylabel('Immigration Scenario')
        ax.set_title('House Price Index Evolution Across Scenarios', fontsize=14, fontweight='bold')

        # Add colorbar
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('Price Index (Base = 100)', rotation=270, labelpad=20)

        # Add text annotations
        for i in range(len(scenarios)):
            for j in range(len(years_sampled)):
                text = ax.text(j, i, f"{price_matrix[i, j]:.0f}",
                             ha="center", va="center", color="black", fontsize=8)

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Saved heatmap to {save_path}")

        plt.tight_layout()
        return fig


def quick_plot(df: pd.DataFrame, scenario: str = "baseline"):
    """
    Quick plot function for Jupyter notebooks.

    Args:
        df: Simulation history DataFrame
        scenario: Scenario name
    """
    viz = Visualizer()
    return viz.plot_simulation_overview(df, scenario)


def compare_scenarios_plot(results: Dict[str, pd.DataFrame]):
    """
    Quick comparison plot for Jupyter notebooks.

    Args:
        results: Dictionary of scenario results
    """
    viz = Visualizer()
    return viz.plot_scenario_comparison(results)
