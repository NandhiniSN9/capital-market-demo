"""Data access layer for performance metrics."""

from datetime import date, datetime, timedelta

from sqlalchemy import case, func, select
from sqlalchemy.exc import DatabaseError
from sqlalchemy.orm import Session

from BE.models.database import Bond, Firm, RFQTrade, WalletShareSnapshot
from BE.settings import WIN_RATE_TREND_DAYS, WOW_COMPARISON_DAYS
from BE.utils.exceptions import DatabaseException
from BE.utils.logger import logger


class PerformanceRepository:
    """Repository for performance-related database queries."""

    def __init__(self, db: Session):
        self.db = db

    def get_current_week_metrics(self, trader_id: str, today: date) -> dict:
        """Aggregate KPI metrics for the current week."""
        week_start = today - timedelta(days=today.weekday())
        return self._aggregate_metrics(trader_id, week_start, today)

    def get_previous_week_metrics(self, trader_id: str, today: date) -> dict:
        """Aggregate KPI metrics for the previous week."""
        week_start = today - timedelta(days=today.weekday())
        prev_start = week_start - timedelta(days=WOW_COMPARISON_DAYS)
        prev_end = week_start - timedelta(days=1)
        return self._aggregate_metrics(trader_id, prev_start, prev_end)

    def _aggregate_metrics(self, trader_id: str, start: date, end: date) -> dict:
        """Run aggregate queries for a date range and return raw metric values."""
        try:
            stmt = (
                select(
                    func.count(RFQTrade.rfq_id).label("total_rfqs"),
                    func.sum(case((RFQTrade.status == "won", 1), else_=0)).label("won_count"),
                    func.sum(RFQTrade.pnl).label("total_pnl"),
                    func.avg(RFQTrade.spread_bps).label("avg_spread"),
                    func.sum(RFQTrade.notional).label("total_volume"),
                    func.avg(RFQTrade.response_time_ms).label("avg_response_time"),
                )
                .where(
                    RFQTrade.trader_id == trader_id,
                    func.date(RFQTrade.rfq_time) >= start,
                    func.date(RFQTrade.rfq_time) <= end,
                )
            )
            row = self.db.execute(stmt).first()
            total_rfqs = row.total_rfqs or 0
            won_count = row.won_count or 0
            return {
                "total_rfqs": total_rfqs,
                "won_count": won_count,
                "win_rate": round((won_count / total_rfqs * 100), 2) if total_rfqs > 0 else 0.0,
                "total_pnl": float(row.total_pnl or 0),
                "avg_spread": round(float(row.avg_spread or 0), 2),
                "total_volume": float(row.total_volume or 0),
                "avg_response_time": round(float(row.avg_response_time or 0), 0),
                "hit_ratio": round((won_count / total_rfqs * 100), 2) if total_rfqs > 0 else 0.0,
            }
        except DatabaseError as e:
            logger.error(f"DB error aggregating metrics for trader={trader_id}: {e}")
            raise DatabaseException() from e

    def get_win_rate_trend(self, trader_id: str, today: date) -> list[dict]:
        """Get daily win rate trend from wallet_share_snapshots for the last 30 days."""
        try:
            start_date = today - timedelta(days=WIN_RATE_TREND_DAYS)
            stmt = (
                select(
                    WalletShareSnapshot.snapshot_date,
                    func.avg(WalletShareSnapshot.win_rate_pct).label("avg_win_rate"),
                )
                .where(
                    WalletShareSnapshot.trader_id == trader_id,
                    WalletShareSnapshot.snapshot_date >= start_date,
                    WalletShareSnapshot.snapshot_date <= today,
                )
                .group_by(WalletShareSnapshot.snapshot_date)
                .order_by(WalletShareSnapshot.snapshot_date)
            )
            rows = self.db.execute(stmt).all()
            return [
                {"date": row.snapshot_date.isoformat(), "win_rate": round(float(row.avg_win_rate), 2)}
                for row in rows
            ]
        except DatabaseError as e:
            logger.error(f"DB error fetching win rate trend for trader={trader_id}: {e}")
            raise DatabaseException() from e

    def get_all_time_metrics(self, trader_id: str) -> dict:
        """Aggregate KPI metrics across all available data for a trader."""
        try:
            stmt = (
                select(
                    func.count(RFQTrade.rfq_id).label("total_rfqs"),
                    func.sum(case((RFQTrade.status == "won", 1), else_=0)).label("won_count"),
                    func.sum(RFQTrade.pnl).label("total_pnl"),
                    func.avg(RFQTrade.spread_bps).label("avg_spread"),
                    func.sum(RFQTrade.notional).label("total_volume"),
                    func.avg(RFQTrade.response_time_ms).label("avg_response_time"),
                )
                .where(RFQTrade.trader_id == trader_id)
            )
            row = self.db.execute(stmt).first()
            total_rfqs = row.total_rfqs or 0
            won_count = row.won_count or 0
            return {
                "total_rfqs": total_rfqs,
                "won_count": won_count,
                "win_rate": round((won_count / total_rfqs * 100), 2) if total_rfqs > 0 else 0.0,
                "total_pnl": float(row.total_pnl or 0),
                "avg_spread": round(float(row.avg_spread or 0), 2),
                "total_volume": float(row.total_volume or 0),
                "avg_response_time": round(float(row.avg_response_time or 0), 0),
                "hit_ratio": round((won_count / total_rfqs * 100), 2) if total_rfqs > 0 else 0.0,
            }
        except DatabaseError as e:
            logger.error(f"DB error aggregating all-time metrics for trader={trader_id}: {e}")
            raise DatabaseException() from e


    def get_half_split_metrics(self, trader_id: str) -> tuple[dict, dict]:
        """Split trades into two halves and return (first_half, second_half) metrics.

        Uses date-based midpoint when trades span multiple days.
        Falls back to row-based split (sorted by rfq_id) when all trades
        share the same date.
        """
        try:
            range_stmt = (
                select(
                    func.min(RFQTrade.rfq_time).label("min_time"),
                    func.max(RFQTrade.rfq_time).label("max_time"),
                    func.count(RFQTrade.rfq_id).label("total"),
                )
                .where(RFQTrade.trader_id == trader_id)
            )
            range_row = self.db.execute(range_stmt).first()

            if not range_row.min_time or not range_row.max_time or range_row.total < 2:
                empty = self._empty_metrics()
                return empty, empty

            min_dt = range_row.min_time
            max_dt = range_row.max_time
            min_date = min_dt.date() if isinstance(min_dt, datetime) else min_dt
            max_date = max_dt.date() if isinstance(max_dt, datetime) else max_dt

            if min_date < max_date:
                # Multi-day data — split by midpoint date
                mid_date = min_date + (max_date - min_date) / 2
                first_half = self._aggregate_metrics(trader_id, min_date, mid_date)
                second_half = self._aggregate_metrics(trader_id, mid_date + timedelta(days=1), max_date)
            else:
                # All trades on the same day — split by row order
                first_half, second_half = self._aggregate_metrics_by_row_split(trader_id)

            return first_half, second_half
        except DatabaseError as e:
            logger.error(f"DB error computing half-split metrics for trader={trader_id}: {e}")
            raise DatabaseException() from e

    def _aggregate_metrics_by_row_split(self, trader_id: str) -> tuple[dict, dict]:
        """Split trades into two halves by rfq_id order and aggregate each half."""
        # Get all rfq_ids sorted
        ids_stmt = (
            select(RFQTrade.rfq_id)
            .where(RFQTrade.trader_id == trader_id)
            .order_by(RFQTrade.rfq_id)
        )
        ids = [r.rfq_id for r in self.db.execute(ids_stmt).all()]

        mid = len(ids) // 2
        first_ids = ids[:mid]
        second_ids = ids[mid:]

        first_half = self._aggregate_metrics_by_ids(trader_id, first_ids)
        second_half = self._aggregate_metrics_by_ids(trader_id, second_ids)
        return first_half, second_half

    def _aggregate_metrics_by_ids(self, trader_id: str, rfq_ids: list[str]) -> dict:
        """Aggregate KPI metrics for a specific set of rfq_ids."""
        if not rfq_ids:
            return self._empty_metrics()
        try:
            stmt = (
                select(
                    func.count(RFQTrade.rfq_id).label("total_rfqs"),
                    func.sum(case((RFQTrade.status == "won", 1), else_=0)).label("won_count"),
                    func.sum(RFQTrade.pnl).label("total_pnl"),
                    func.avg(RFQTrade.spread_bps).label("avg_spread"),
                    func.sum(RFQTrade.notional).label("total_volume"),
                    func.avg(RFQTrade.response_time_ms).label("avg_response_time"),
                )
                .where(
                    RFQTrade.trader_id == trader_id,
                    RFQTrade.rfq_id.in_(rfq_ids),
                )
            )
            row = self.db.execute(stmt).first()
            total_rfqs = row.total_rfqs or 0
            won_count = row.won_count or 0
            return {
                "total_rfqs": total_rfqs,
                "won_count": won_count,
                "win_rate": round((won_count / total_rfqs * 100), 2) if total_rfqs > 0 else 0.0,
                "total_pnl": float(row.total_pnl or 0),
                "avg_spread": round(float(row.avg_spread or 0), 2),
                "total_volume": float(row.total_volume or 0),
                "avg_response_time": round(float(row.avg_response_time or 0), 0),
                "hit_ratio": round((won_count / total_rfqs * 100), 2) if total_rfqs > 0 else 0.0,
            }
        except DatabaseError as e:
            logger.error(f"DB error aggregating metrics by IDs for trader={trader_id}: {e}")
            raise DatabaseException() from e

    @staticmethod
    def _empty_metrics() -> dict:
        """Return a zeroed-out metrics dict."""
        return {
            "total_rfqs": 0, "won_count": 0, "win_rate": 0.0,
            "total_pnl": 0.0, "avg_spread": 0.0, "total_volume": 0.0,
            "avg_response_time": 0.0, "hit_ratio": 0.0,
        }

    def get_win_rate_trend_all(self, trader_id: str) -> list[dict]:
        """Get all available win rate trend data from wallet_share_snapshots."""
        try:
            stmt = (
                select(
                    WalletShareSnapshot.snapshot_date,
                    func.avg(WalletShareSnapshot.win_rate_pct).label("avg_win_rate"),
                )
                .where(WalletShareSnapshot.trader_id == trader_id)
                .group_by(WalletShareSnapshot.snapshot_date)
                .order_by(WalletShareSnapshot.snapshot_date)
            )
            rows = self.db.execute(stmt).all()
            return [
                {"date": row.snapshot_date.isoformat(), "win_rate": round(float(row.avg_win_rate), 2)}
                for row in rows
            ]
        except DatabaseError as e:
            logger.error(f"DB error fetching win rate trend for trader={trader_id}: {e}")
            raise DatabaseException() from e

    def get_scatter_data(self, trader_id: str) -> list[dict]:
        """Get spread vs market scatter data from rfq_trades joined with bonds and firms."""
        try:
            stmt = (
                select(
                    RFQTrade.rfq_id,
                    RFQTrade.vs_mkt_bps,
                    RFQTrade.execution_quality,
                    RFQTrade.notional,
                    RFQTrade.status,
                    Bond.bond_display,
                    Firm.name.label("counterparty_name"),
                )
                .join(Bond, RFQTrade.bond_id == Bond.bond_id)
                .join(Firm, RFQTrade.counterparty_id == Firm.firm_id)
                .where(RFQTrade.trader_id == trader_id)
            )
            rows = self.db.execute(stmt).all()
            return [
                {
                    "trade_id": row.rfq_id,
                    "spread_vs_market": round(float(row.vs_mkt_bps or 0), 2),
                    "trade_outcome_score": round(float(row.execution_quality or 0), 2),
                    "notional": float(row.notional or 0),
                    "status": row.status.upper() if row.status else "PENDING",
                    "security": row.bond_display or "",
                    "counterparty": row.counterparty_name or "",
                }
                for row in rows
            ]
        except DatabaseError as e:
            logger.error(f"DB error fetching scatter data for trader={trader_id}: {e}")
            raise DatabaseException() from e
