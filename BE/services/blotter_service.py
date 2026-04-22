"""Business logic for the trade blotter endpoint."""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from BE.models.schemas import (
    CounterpartyInfo,
    FiltersApplied,
    NotionalInfo,
    PnlInfo,
    SecurityInfo,
    Trade,
    TradeBlotterRequest,
    TradeBlotterResponse,
    VsMktInfo,
)
from BE.repositories.blotter_repository import BlotterRepository
from BE.settings import DEFAULT_SORT_DIRECTION, DEFAULT_SORT_FIELD
from BE.utils.logger import logger


class BlotterService:
    """Orchestrates trade blotter search, filtering, and response assembly."""

    def __init__(self, db: Session):
        self.repo = BlotterRepository(db)

    def search_blotter(self, request: TradeBlotterRequest) -> TradeBlotterResponse:
        """Execute blotter search and build the response."""
        sort_field = DEFAULT_SORT_FIELD
        sort_direction = DEFAULT_SORT_DIRECTION
        if request.sort:
            sort_field = request.sort.field or DEFAULT_SORT_FIELD
            sort_direction = request.sort.direction or DEFAULT_SORT_DIRECTION

        status_filter = None
        asset_class_filter = None
        if request.filters:
            status_filter = request.filters.status
            asset_class_filter = request.filters.asset_class

        raw_trades = self.repo.search_trades(
            trader_id=request.trader_id,
            search=request.search,
            status_filter=status_filter,
            asset_class_filter=asset_class_filter,
            sort_field=sort_field,
            sort_direction=sort_direction,
        )

        trades = [self._map_trade(t) for t in raw_trades]

        filters_applied = None
        if request.filters:
            filters_applied = FiltersApplied(
                status=request.filters.status,
                asset_class=request.filters.asset_class,
            )

        logger.info(
            f"Blotter search completed for trader={request.trader_id}, results={len(trades)}, search={request.search}"
        )

        return TradeBlotterResponse(
            status="success",
            timestamp=datetime.now(timezone.utc).isoformat(),
            trader_id=request.trader_id,
            search_applied=request.search,
            filters_applied=filters_applied,
            total_count=len(trades),
            trades=trades,
        )

    @staticmethod
    def _map_trade(row: dict) -> Trade:
        """Map a raw database row dict to a Trade response model."""
        notional_val = row["notional"]
        pnl_val = row["pnl"]
        vs_mkt_val = row["vs_mkt_bps"]

        return Trade(
            rfq_id=row["rfq_id"],
            time=row["time"],
            security=SecurityInfo(
                bond_display=row["bond_display"],
                bond_id=row["bond_id"],
                asset_class=row["asset_class"],
            ),
            side=row["side"],
            notional=NotionalInfo(
                value=notional_val,
                display=_format_currency(notional_val),
            ),
            spread=row["spread_bps"],
            vs_mkt=VsMktInfo(
                value=vs_mkt_val,
                direction="above" if vs_mkt_val >= 0 else "below",
            ),
            counterparty=CounterpartyInfo(
                firm_id=row["counterparty_firm_id"],
                name=row["counterparty_name"],
            ),
            venue=row["venue"],
            status=row["status"],
            pnl=PnlInfo(
                value=pnl_val,
                display=_format_pnl(pnl_val),
            ),
        )


def _format_currency(value: float) -> str:
    """Format a notional value to human-readable string (e.g. $2.0M, $500K)."""
    abs_val = abs(value)
    if abs_val >= 1_000_000_000:
        return f"${value / 1_000_000_000:.1f}B"
    if abs_val >= 1_000_000:
        return f"${value / 1_000_000:.1f}M"
    if abs_val >= 1_000:
        return f"${value / 1_000:.0f}K"
    return f"${value:,.0f}"


def _format_pnl(value: float) -> str:
    """Format P&L value with sign and dollar symbol."""
    if value == 0:
        return "$0"
    return f"${value:+,.0f}"
