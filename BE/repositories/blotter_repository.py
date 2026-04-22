"""Data access layer for the trade blotter."""

from sqlalchemy import asc, desc, func, select
from sqlalchemy.exc import DatabaseError
from sqlalchemy.orm import Session

from BE.models.database import Bond, Firm, RFQTrade
from BE.utils.exceptions import DatabaseException
from BE.utils.logger import logger

# Mapping of API sort field names to ORM columns
SORT_COLUMN_MAP = {
    "time": RFQTrade.rfq_time,
    "security": Bond.bond_display,
    "side": RFQTrade.side,
    "notional": RFQTrade.notional,
    "spread": RFQTrade.spread_bps,
    "vs_mkt": RFQTrade.vs_mkt_bps,
    "counterparty": Firm.name,
    "venue": RFQTrade.venue,
    "status": RFQTrade.status,
    "pnl": RFQTrade.pnl,
}


class BlotterRepository:
    """Repository for trade blotter database queries."""

    def __init__(self, db: Session):
        self.db = db

    def search_trades(
        self,
        trader_id: str,
        search: str | None = None,
        status_filter: list[str] | None = None,
        asset_class_filter: list[str] | None = None,
        sort_field: str = "time",
        sort_direction: str = "desc",
    ) -> list[dict]:
        """Query trades with optional search, filters, and sorting."""
        try:
            stmt = (
                select(
                    RFQTrade.rfq_id,
                    RFQTrade.rfq_time,
                    Bond.bond_display,
                    Bond.bond_id,
                    Bond.asset_class,
                    RFQTrade.side,
                    RFQTrade.notional,
                    RFQTrade.spread_bps,
                    RFQTrade.vs_mkt_bps,
                    Firm.firm_id.label("counterparty_firm_id"),
                    Firm.name.label("counterparty_name"),
                    RFQTrade.venue,
                    RFQTrade.status,
                    RFQTrade.pnl,
                )
                .join(Bond, RFQTrade.bond_id == Bond.bond_id)
                .join(Firm, RFQTrade.counterparty_id == Firm.firm_id)
                .where(RFQTrade.trader_id == trader_id)
            )

            if search:
                search_term = f"%{search.lower()}%"
                stmt = stmt.where(
                    func.lower(Bond.bond_display).like(search_term)
                    | func.lower(Firm.name).like(search_term)
                    | func.lower(RFQTrade.rfq_id).like(search_term)
                )

            if status_filter:
                normalized = [s.lower() for s in status_filter]
                stmt = stmt.where(func.lower(RFQTrade.status).in_(normalized))

            if asset_class_filter:
                stmt = stmt.where(Bond.asset_class.in_(asset_class_filter))

            sort_col = SORT_COLUMN_MAP.get(sort_field, RFQTrade.rfq_time)
            order_fn = desc if sort_direction == "desc" else asc
            stmt = stmt.order_by(order_fn(sort_col))

            rows = self.db.execute(stmt).all()

            return [
                {
                    "rfq_id": row.rfq_id,
                    "time": row.rfq_time.strftime("%Y-%m-%dT%H:%M:%S.000Z") if row.rfq_time else "",
                    "bond_display": row.bond_display or "",
                    "bond_id": row.bond_id or "",
                    "asset_class": row.asset_class or "",
                    "side": row.side.upper() if row.side else "",
                    "notional": float(row.notional or 0),
                    "spread_bps": float(row.spread_bps or 0),
                    "vs_mkt_bps": float(row.vs_mkt_bps or 0),
                    "counterparty_firm_id": row.counterparty_firm_id or "",
                    "counterparty_name": row.counterparty_name or "",
                    "venue": row.venue or "",
                    "status": row.status or "",
                    "pnl": float(row.pnl or 0),
                }
                for row in rows
            ]
        except DatabaseError as e:
            logger.error(f"DB error searching trades for trader={trader_id}: {e}")
            raise DatabaseException() from e
