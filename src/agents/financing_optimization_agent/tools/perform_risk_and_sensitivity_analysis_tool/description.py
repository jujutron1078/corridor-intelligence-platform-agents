TOOL_DESCRIPTION = """
Conducts sensitivity analysis and Monte Carlo simulations. Identifies critical
assumptions and generates tornado diagrams to show the impact of variables on the IRR.
Accepts financial model data from the build_financial_model tool and optional
variable variances (e.g. capex, revenue, interest_rate). Returns Monte Carlo results
(probability of IRR above 12%, P50/P90 IRR), critical risks, and a summary message.
"""
