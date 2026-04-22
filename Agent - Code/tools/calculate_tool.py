"""Financial calculation tool — all formulas for Credit, DCM, and Private Markets analysts."""

from __future__ import annotations


def calculate(formula_name: str, **kwargs: float) -> dict:
    """Execute a financial formula by name."""
    if formula_name not in FORMULA_REGISTRY:
        available = ", ".join(sorted(FORMULA_REGISTRY.keys()))
        raise ValueError(f"Unknown formula '{formula_name}'. Available: {available}")
    func, required_inputs, unit = FORMULA_REGISTRY[formula_name]
    missing = [k for k in required_inputs if k not in kwargs]
    if missing:
        raise ValueError(f"Missing inputs for '{formula_name}': {missing}")
    result = func(**{k: kwargs[k] for k in required_inputs})
    return {
        "formula": formula_name,
        "inputs": {k: kwargs[k] for k in required_inputs},
        "result": round(result, 4) if isinstance(result, float) else result,
        "unit": unit,
    }


# Credit — Balance Sheet
def _current_ratio(current_assets: float, current_liabilities: float) -> float:
    return current_assets / current_liabilities

def _quick_ratio(current_assets: float, inventory: float, current_liabilities: float) -> float:
    return (current_assets - inventory) / current_liabilities

def _working_capital(current_assets: float, current_liabilities: float) -> float:
    return current_assets - current_liabilities

def _debt_to_equity(total_debt: float, total_equity: float) -> float:
    return total_debt / total_equity

def _debt_to_assets(total_debt: float, total_assets: float) -> float:
    return total_debt / total_assets

# Credit — Income Statement
def _gross_margin(gross_profit: float, revenue: float) -> float:
    return gross_profit / revenue

def _operating_margin(operating_income: float, revenue: float) -> float:
    return operating_income / revenue

def _net_profit_margin(net_income: float, revenue: float) -> float:
    return net_income / revenue

def _ebitda_margin(ebitda: float, revenue: float) -> float:
    return ebitda / revenue

def _return_on_assets(net_income: float, total_assets: float) -> float:
    return net_income / total_assets

def _return_on_equity(net_income: float, preferred_dividends: float, avg_common_equity: float) -> float:
    return (net_income - preferred_dividends) / avg_common_equity

# Credit — Cash Flow
def _operating_cash_flow_ratio(operating_cash_flow: float, current_liabilities: float) -> float:
    return operating_cash_flow / current_liabilities

def _free_cash_flow(operating_cash_flow: float, capital_expenditures: float) -> float:
    return operating_cash_flow - capital_expenditures

def _cash_flow_to_debt(operating_cash_flow: float, total_debt: float) -> float:
    return operating_cash_flow / total_debt

def _dscr(operating_cash_flow: float, total_debt_service: float) -> float:
    return operating_cash_flow / total_debt_service

# Credit — Covenant (Leverage)
def _total_leverage_ratio(total_debt: float, ebitda: float) -> float:
    return total_debt / ebitda

def _net_leverage_ratio(total_debt: float, cash: float, ebitda: float) -> float:
    return (total_debt - cash) / ebitda

def _secured_leverage_ratio(secured_debt: float, ebitda: float) -> float:
    return secured_debt / ebitda

# Credit — Covenant (Coverage)
def _interest_coverage(ebit: float, interest_expense: float) -> float:
    return ebit / interest_expense

def _fixed_charge_coverage(ebit: float, fixed_charges: float, interest: float) -> float:
    return (ebit + fixed_charges) / (fixed_charges + interest)

# DCM
def _net_debt(total_debt: float, cash: float) -> float:
    return total_debt - cash

def _debt_to_capitalization(total_debt: float, total_capitalization: float) -> float:
    return total_debt / total_capitalization

def _debt_to_ebitda(total_debt: float, ebitda: float) -> float:
    return total_debt / ebitda

def _ebitda_interest_coverage(ebitda: float, interest_expense: float) -> float:
    return ebitda / interest_expense

def _fcf_to_debt(operating_cash_flow: float, capital_expenditures: float, total_debt: float) -> float:
    return (operating_cash_flow - capital_expenditures) / total_debt

# Private Markets
def _ltm_value(q1: float, q2: float, q3: float, q4: float) -> float:
    return q1 + q2 + q3 + q4

def _revenue_cagr_3yr(revenue_year_0: float, revenue_year_3: float) -> float:
    return (revenue_year_3 / revenue_year_0) ** (1 / 3) - 1

def _revenue_cagr_5yr(revenue_year_0: float, revenue_year_5: float) -> float:
    return (revenue_year_5 / revenue_year_0) ** (1 / 5) - 1

def _rule_of_40(revenue_growth_pct: float, ebitda_margin_pct: float) -> float:
    return revenue_growth_pct + ebitda_margin_pct

def _customer_concentration(top_customer_revenue: float, total_revenue: float) -> float:
    return top_customer_revenue / total_revenue


# Formula Registry — maps name → (function, required_inputs, unit)
FORMULA_REGISTRY: dict[str, tuple] = {
    "current_ratio": (_current_ratio, ["current_assets", "current_liabilities"], "x"),
    "quick_ratio": (_quick_ratio, ["current_assets", "inventory", "current_liabilities"], "x"),
    "working_capital": (_working_capital, ["current_assets", "current_liabilities"], "$"),
    "debt_to_equity": (_debt_to_equity, ["total_debt", "total_equity"], "x"),
    "debt_to_assets": (_debt_to_assets, ["total_debt", "total_assets"], "x"),
    "gross_margin": (_gross_margin, ["gross_profit", "revenue"], "%"),
    "operating_margin": (_operating_margin, ["operating_income", "revenue"], "%"),
    "net_profit_margin": (_net_profit_margin, ["net_income", "revenue"], "%"),
    "ebitda_margin": (_ebitda_margin, ["ebitda", "revenue"], "%"),
    "return_on_assets": (_return_on_assets, ["net_income", "total_assets"], "%"),
    "return_on_equity": (_return_on_equity, ["net_income", "preferred_dividends", "avg_common_equity"], "%"),
    "operating_cash_flow_ratio": (_operating_cash_flow_ratio, ["operating_cash_flow", "current_liabilities"], "x"),
    "free_cash_flow": (_free_cash_flow, ["operating_cash_flow", "capital_expenditures"], "$"),
    "cash_flow_to_debt": (_cash_flow_to_debt, ["operating_cash_flow", "total_debt"], "x"),
    "dscr": (_dscr, ["operating_cash_flow", "total_debt_service"], "x"),
    "total_leverage_ratio": (_total_leverage_ratio, ["total_debt", "ebitda"], "x"),
    "net_leverage_ratio": (_net_leverage_ratio, ["total_debt", "cash", "ebitda"], "x"),
    "secured_leverage_ratio": (_secured_leverage_ratio, ["secured_debt", "ebitda"], "x"),
    "interest_coverage": (_interest_coverage, ["ebit", "interest_expense"], "x"),
    "fixed_charge_coverage": (_fixed_charge_coverage, ["ebit", "fixed_charges", "interest"], "x"),
    "net_debt": (_net_debt, ["total_debt", "cash"], "$"),
    "debt_to_capitalization": (_debt_to_capitalization, ["total_debt", "total_capitalization"], "x"),
    "debt_to_ebitda": (_debt_to_ebitda, ["total_debt", "ebitda"], "x"),
    "ebitda_interest_coverage": (_ebitda_interest_coverage, ["ebitda", "interest_expense"], "x"),
    "fcf_to_debt": (_fcf_to_debt, ["operating_cash_flow", "capital_expenditures", "total_debt"], "x"),
    "ltm_revenue": (_ltm_value, ["q1", "q2", "q3", "q4"], "$"),
    "ltm_ebitda": (_ltm_value, ["q1", "q2", "q3", "q4"], "$"),
    "revenue_cagr_3yr": (_revenue_cagr_3yr, ["revenue_year_0", "revenue_year_3"], "%"),
    "revenue_cagr_5yr": (_revenue_cagr_5yr, ["revenue_year_0", "revenue_year_5"], "%"),
    "rule_of_40": (_rule_of_40, ["revenue_growth_pct", "ebitda_margin_pct"], "score"),
    "customer_concentration": (_customer_concentration, ["top_customer_revenue", "total_revenue"], "%"),
}


def list_formulas() -> list[str]:
    """Return all available formula names."""
    return sorted(FORMULA_REGISTRY.keys())


def describe_formulas() -> str:
    """Return a description of every formula with its required inputs."""
    lines: list[str] = []
    for name in sorted(FORMULA_REGISTRY):
        _, required_inputs, unit = FORMULA_REGISTRY[name]
        lines.append(f"- {name}(inputs: {', '.join(required_inputs)}) -> {unit}")
    return "\n".join(lines)
