"""Enums and mappings for the Deal Intelligence Agent."""

from __future__ import annotations

from enum import Enum


class AnalystType(str, Enum):
    buy_side = "buy_side"
    sell_side = "sell_side"
    credit = "credit"
    dcm = "dcm"
    private_markets = "private_markets"


class ScenarioType(str, Enum):
    default = "default"
    pre_earnings = "pre_earnings"
    earnings_day = "earnings_day"
    earnings_call = "earnings_call"
    post_earnings = "post_earnings"
    balance_sheet_analysis = "balance_sheet_analysis"
    income_statement_analysis = "income_statement_analysis"
    cash_flow_analysis = "cash_flow_analysis"
    covenant_analysis = "covenant_analysis"
    issuer_creditworthiness = "issuer_creditworthiness"
    debt_service_capacity = "debt_service_capacity"
    refinancing_risk = "refinancing_risk"
    market_terms_analysis = "market_terms_analysis"
    exploratory_due_diligence = "exploratory_due_diligence"
    confirmatory_due_diligence = "confirmatory_due_diligence"


class AgentType(str, Enum):
    deal = "deal"


class FileType(str, Enum):
    pdf = "pdf"
    pptx = "pptx"
    docx = "docx"


class DocumentCategory(str, Enum):
    financial_statement = "financial_statement"
    legal = "legal"
    operational = "operational"
    market = "market"


class ProcessingStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    ready = "ready"
    failed = "failed"


class ChatStatus(str, Enum):
    active = "active"
    in_progress = "in_progress"
    completed = "completed"
    failed = "failed"


class ConversationStatus(str, Enum):
    in_progress = "in_progress"
    completed = "completed"
    failed = "failed"


class MessageRole(str, Enum):
    user = "user"
    assistant = "assistant"


class ConfidenceLevel(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"


class ChunkType(str, Enum):
    text = "text"
    table = "table"
    chart = "chart"


ANALYST_SCENARIO_MAPPING: dict[AnalystType, list[ScenarioType]] = {
    AnalystType.buy_side: [
        ScenarioType.default, ScenarioType.pre_earnings, ScenarioType.earnings_day,
        ScenarioType.earnings_call, ScenarioType.post_earnings,
    ],
    AnalystType.sell_side: [
        ScenarioType.default, ScenarioType.pre_earnings, ScenarioType.earnings_day,
        ScenarioType.earnings_call, ScenarioType.post_earnings,
    ],
    AnalystType.credit: [
        ScenarioType.default, ScenarioType.balance_sheet_analysis,
        ScenarioType.income_statement_analysis, ScenarioType.cash_flow_analysis,
        ScenarioType.covenant_analysis,
    ],
    AnalystType.dcm: [
        ScenarioType.default, ScenarioType.issuer_creditworthiness,
        ScenarioType.debt_service_capacity, ScenarioType.refinancing_risk,
        ScenarioType.market_terms_analysis,
    ],
    AnalystType.private_markets: [
        ScenarioType.default, ScenarioType.exploratory_due_diligence,
        ScenarioType.confirmatory_due_diligence,
    ],
}
