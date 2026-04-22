"""Pydantic models for API request/response schemas."""

from pydantic import BaseModel, ConfigDict, Field

# ── Performance Response Models ──


class MetricCard(BaseModel):
    """Single KPI card in the performance overview."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    label: str
    """Display label for the KPI card."""

    value: float
    """Current metric value."""

    unit: str
    """Unit of measure (%, $, bps, ms)."""

    delta: float
    """Week-over-week change value."""

    delta_label: str = Field("vs last week", alias="deltaLabel")
    """Human-readable label for the delta comparison period."""

    trend: str
    """Direction of change: up, down, or flat."""

    format: str
    """Formatting hint: percent, currency, bps, ms."""


class WinRateTrendPoint(BaseModel):
    """Single data point in the 30-day win rate trend."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    date: str
    """Date of the data point (YYYY-MM-DD)."""

    win_rate: float = Field(..., alias="winRate")
    """Win rate percentage on that date."""


class ScatterDataPoint(BaseModel):
    """Single point in the spread vs market scatter plot."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    trade_id: str = Field(..., alias="tradeId")
    """Trade identifier shown on hover."""

    spread_vs_market: float = Field(..., alias="spreadVsMarket")
    """X-axis: quoted spread minus TRACE benchmark (bps)."""

    trade_outcome_score: float = Field(..., alias="tradeOutcomeScore")
    """Y-axis: execution quality score (-1 to 1)."""

    notional: float
    """Trade notional in USD."""

    status: str
    """WON, LOST, PENDING, or CANCELLED."""

    security: str
    """Bond display name."""

    counterparty: str
    """Counterparty firm name."""


class PerformanceResponse(BaseModel):
    """Full response for GET /performance."""

    model_config = ConfigDict(populate_by_name=True)

    status: str = "success"
    timestamp: str
    """ISO 8601 timestamp of the response."""

    trader_id: str
    date: str
    """Current date (YYYY-MM-DD)."""

    metrics: list[MetricCard]
    """Array of 6 KPI metric cards."""

    win_rate_trend: list[WinRateTrendPoint] = Field(..., alias="winRateTrend")
    """Daily win rate trend data points (30 days)."""

    scatter_data: list[ScatterDataPoint] = Field(..., alias="scatterData")
    """Scatter plot data for spread vs market chart."""


# ── Trade Blotter Models ──


class TradeBlotterFilters(BaseModel):
    """Chip-toggle filters for the trade blotter."""

    status: list[str] | None = None
    """Filter by status: WON, LOST, PENDING, CANCELLED."""

    asset_class: list[str] | None = None
    """Filter by asset class: IG_CORP, HY_CORP, GOVT, MBS, ABS."""


class TradeBlotterSort(BaseModel):
    """Sort configuration for the trade blotter."""

    field: str = "time"
    """Column to sort by."""

    direction: str = "desc"
    """Sort direction: asc or desc."""


class TradeBlotterRequest(BaseModel):
    """POST body for /trade-blotter."""

    trader_id: str
    """Trader identifier."""

    search: str | None = None
    """Free-text search across security, counterparty, rfq_id."""

    filters: TradeBlotterFilters | None = None
    """Toggle-chip filters."""

    sort: TradeBlotterSort | None = None
    """Sort configuration."""


class SecurityInfo(BaseModel):
    """Bond security info nested in a trade row."""

    bond_display: str
    """Formatted: TICKER COUPON MM/DD/YYYY."""

    bond_id: str
    """FK to bonds table."""

    asset_class: str
    """IG_CORP, HY_CORP, GOVT, MBS, ABS."""


class NotionalInfo(BaseModel):
    """Notional value with display formatting."""

    value: float
    """Raw USD value."""

    display: str
    """Human-readable (e.g. $2.0M)."""


class VsMktInfo(BaseModel):
    """Spread vs market benchmark info."""

    value: float
    """Signed bps value."""

    direction: str
    """above or below market."""


class CounterpartyInfo(BaseModel):
    """Counterparty firm info."""

    firm_id: str
    """FK to firms table."""

    name: str
    """Firm display name."""


class PnlInfo(BaseModel):
    """P&L value with display formatting."""

    value: float
    """Raw USD value."""

    display: str
    """Human-readable (e.g. $1,500)."""


class Trade(BaseModel):
    """Single trade row in the blotter."""

    rfq_id: str
    time: str
    """ISO 8601 datetime."""

    security: SecurityInfo
    side: str
    """BUY or SELL."""

    notional: NotionalInfo
    spread: float
    """Quoted spread in bps."""

    vs_mkt: VsMktInfo
    counterparty: CounterpartyInfo
    venue: str
    status: str
    pnl: PnlInfo


class FiltersApplied(BaseModel):
    """Echo of active filters in the response."""

    status: list[str] | None = None
    asset_class: list[str] | None = None


class TradeBlotterResponse(BaseModel):
    """Full response for POST /trade-blotter."""

    status: str = "success"
    timestamp: str
    trader_id: str
    search_applied: str | None = None
    filters_applied: FiltersApplied | None = None
    total_count: int
    """Total number of trades matching the query."""

    trades: list[Trade]


# ── Session Models ──

VALID_INTELLIGENCE = {"rfq"}
VALID_PERSONAS = {"sales_trader", "credit_trader", "portfolio_manager"}
VALID_SIMULATIONS = {"Pre-Market Preparation", "Post-Trade Analysis", "Client Review", "Axes Optimization"}
VALID_AGENT_TYPES = {"deal", "rfq"}


class SessionRequest(BaseModel):
    """POST body for /session — create or continue a chat session."""

    session_id: str | None = None
    """Omit to create a new session. Provide to continue an existing one."""

    user_id: str
    """Trader/user identifier from users table."""

    intelligence: str
    """Intelligence domain context (e.g. rfq)."""

    user_persona: str
    """Role-based persona: sales_trader, credit_trader, portfolio_manager."""

    simulation: str
    """Simulation context determining agent behavior."""

    session_title: str | None = None
    """Optional title for the session."""

    agent_type: str = "rfq"
    """Agent type: deal or rfq."""

    chat_message: str | None = None
    """User message. Defaults to system-generated prompt on session creation."""


class SessionAckResponse(BaseModel):
    """Acknowledgement response for POST /session."""

    status: str = "success"
    session_id: str
    """Session identifier (generated on creation, echoed on continuation)."""

    conversation_id: str
    """Conversation turn ID — poll GET /conversation/{conversation_id} for the response."""

    response_status: str = "InProgress"
    """Always InProgress — agent is generating the response asynchronously."""

    timestamp: str
    """ISO 8601 datetime when the session was created or message was accepted."""


class ConversationResponse(BaseModel):
    """Flat conversation response — used for both polling and history."""

    session_id: str
    conversation_id: str
    """Unique ID for this conversation turn."""

    user_message: str | None = None
    """The user's original message for this turn."""

    response_message: str | dict | None = None
    """Agent's response payload. Null while InProgress."""

    response_status: str
    """InProgress or Completed."""

    timestamp: str
    """ISO 8601 datetime when this conversation turn was created."""


class ConversationListResponse(BaseModel):
    """Response for GET /session/{session_id}/conversations."""

    status: str = "success"
    session_id: str
    conversations: list[ConversationResponse]
