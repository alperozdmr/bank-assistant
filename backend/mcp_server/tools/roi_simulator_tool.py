import pandas as pd
import numpy as np
import re

class ROISimulatorTool:
    """
    Uses historical asset performance data and predefined portfolio mixes to simulate
    potential future investment returns using a Monte Carlo simulation method.
    """

    def __init__(self, repo):
        """
        Initializes the tool by fetching data via the provided repository object.

        Args:
            repo: An instance of a repository class (e.g., SQLiteRepository)
                  that has get_asset_performance_data() and get_portfolio_mixes_data() methods.
        """
        print("Initializing ROISimulatorTool...")
        self.repo = repo
        df_assets = self.repo.get_asset_performance_data()
        df_portfolios = self.repo.get_portfolio_mixes_data()

        if df_assets.empty or df_portfolios.empty:
            raise ValueError("DataFrames for assets and portfolios cannot be empty.")
            
        self.df_assets = df_assets.set_index('varlik_sinifi')
        self.df_portfolios = df_portfolios
        self._prepare_portfolio_data()

    def _parse_allocation_string(self, allocation_str: str) -> dict:
        allocations = {}
        pattern = re.compile(r'%(\d+)\s*([^,]+)')
        matches = pattern.findall(allocation_str)
        
        for percentage, asset_name in matches:
            allocations[asset_name.strip()] = float(percentage)
            
        total_percentage = sum(allocations.values())
        if total_percentage > 0:
            for asset in allocations:
                allocations[asset] = (allocations[asset] / total_percentage) * 100
        return allocations

    def _prepare_portfolio_data(self):
        self.df_portfolios['parsed_allocation'] = self.df_portfolios['varlik_dagilimi'].apply(self._parse_allocation_string)
        print("Portfolio data has been prepared and parsed.")

    def run(self, portfolio_name: str, monthly_investment: float, years: int, num_simulations: int = 1000) -> dict:
        portfolio_series = self.df_portfolios[self.df_portfolios['portfoy_adi'] == portfolio_name]
        if portfolio_series.empty:
            return {"error": f"Portfolio '{portfolio_name}' not found."}
        
        asset_mix = portfolio_series.iloc[0]['parsed_allocation']
        if not asset_mix:
             return {"error": f"Could not parse asset allocation for portfolio '{portfolio_name}'."}

        portfolio_return = 0
        portfolio_volatility = 0
        
        for asset, percentage in asset_mix.items():
            weight = percentage / 100.0
            try:
                asset_stats = self.df_assets.loc[asset]
                portfolio_return += weight * (asset_stats['ortalama_yillik_getiri'] / 100.0)
                portfolio_volatility += weight * (asset_stats['yillik_volatilite'] / 100.0)
            except KeyError:
                return {"error": f"Asset '{asset}' found in portfolio mix but not in asset performance data."}

        monthly_return = (1 + portfolio_return)**(1/12) - 1
        monthly_volatility = portfolio_volatility / np.sqrt(12)
        
        final_balances = []
        num_months = years * 12

        for _ in range(num_simulations):
            current_balance = 0
            for _ in range(num_months):
                random_shock = np.random.normal(0, 1)
                month_return = monthly_return + random_shock * monthly_volatility
                
                current_balance += monthly_investment
                current_balance *= (1 + month_return)
            
            final_balances.append(current_balance)
            
        avg_final_balance = np.mean(final_balances)
        percentile_25 = np.percentile(final_balances, 25)
        percentile_75 = np.percentile(final_balances, 75)
        
        return {
            "portfolio_name": portfolio_name,
            "years": years,
            "monthly_investment": monthly_investment,
            "average_outcome": round(avg_final_balance, 2),
            "good_scenario_outcome (75th percentile)": round(percentile_75, 2),
            "bad_scenario_outcome (25th percentile)": round(percentile_25, 2),
            "num_simulations_run": num_simulations,
            "ui_component": {
                "type": "roi_simulation_card",
                "portfolio_name": portfolio_name,
                "years": years,
                "monthly_investment": monthly_investment,
                "average_outcome": round(avg_final_balance, 2),
                "good_scenario_outcome": round(percentile_75, 2),
                "bad_scenario_outcome": round(percentile_25, 2),
                "num_simulations_run": num_simulations
            }
        }
