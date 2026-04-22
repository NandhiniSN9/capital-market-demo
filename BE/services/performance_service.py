"""Business logic for the performance overview endpoint."""

from datetime import date, datetime, timezone

from sqlalchemy.orm import Session

from BE.models.schemas import (
    MetricCard,
    PerformanceResponse,
    ScatterDataPoint,
    WinRateTrendPoint,
)
from BE.repositories.performance_repository import PerformanceRepository
from BE.settings import (
    KPI_AVG_RESPONSE,
    KPI_AVG_SPREAD,
    KPI_HIT_RATIO,
    KPI_TOTAL_PNL,
    KPI_TOTAL_VOLUME,
    KPI_WIN_RATE,
)
from BE.utils.logger import logger


class PerformanceService:
    """Orchestrates KPI computation and response assembly."""

    def __init__(self, db: Session):
        self.repo = PerformanceRepository(db)

    def get_performance(self, trader_id: str) -> PerformanceResponse:
        """Build the full performance response with KPIs, trend, and scatter data."""
        today = date.today()

        current = self.repo.get_all_time_metrics(trader_id)
        first_half, second_half = self.repo.get_half_split_metrics(trader_id)

        metrics = self._build_metric_cards_dynamic(current, first_half, second_half)
        trend = self._build_trend_all(trader_id)
        scatter = self._build_scatter(trader_id)

        logger.info(f"Performance data assembled for trader={trader_id}, date={today}")

        return PerformanceResponse(
            status="success",
            timestamp=datetime.now(timezone.utc).isoformat(),
            trader_id=trader_id,
            date=today.isoformat(),
            metrics=metrics,
            win_rate_trend=trend,
            scatter_data=scatter,
        )

    def _build_metric_cards_dynamic(
        self, all_time: dict, first_half: dict, second_half: dict
    ) -> list[MetricCard]:
        """Build 6 KPI cards with all-time values and first-half vs second-half deltas."""
        definitions = [
            (KPI_WIN_RATE, "win_rate", "%", "percent"),
            (KPI_TOTAL_PNL, "total_pnl", "$", "currency"),
            (KPI_AVG_SPREAD, "avg_spread", "bps", "bps"),
            (KPI_TOTAL_VOLUME, "total_volume", "$", "currency"),
            (KPI_AVG_RESPONSE, "avg_response_time", "ms", "ms"),
            (KPI_HIT_RATIO, "hit_ratio", "%", "percent"),
        ]

        cards = []
        for label, key, unit, fmt in definitions:
            value = all_time.get(key, 0)
            prev_val = first_half.get(key, 0)
            cur_val = second_half.get(key, 0)
            delta = self._compute_delta(cur_val, prev_val)
            trend = self._determine_trend(delta, key)
            cards.append(
                MetricCard(
                    label=label,
                    value=value,
                    unit=unit,
                    delta=delta,
                    delta_label="vs prior period",
                    trend=trend,
                    format=fmt,
                )
            )
        return cards

    def _build_trend_all(self, trader_id: str) -> list[WinRateTrendPoint]:
        """Build win rate trend from all available wallet share snapshots."""
        raw = self.repo.get_win_rate_trend_all(trader_id)
        return [WinRateTrendPoint(date=r["date"], win_rate=r["win_rate"]) for r in raw]

    def _build_metric_cards(self, current: dict, previous: dict) -> list[MetricCard]:
        """Compute 6 KPI cards with week-over-week deltas."""
        definitions = [
            (KPI_WIN_RATE, "win_rate", "%", "percent"),
            (KPI_TOTAL_PNL, "total_pnl", "$", "currency"),
            (KPI_AVG_SPREAD, "avg_spread", "bps", "bps"),
            (KPI_TOTAL_VOLUME, "total_volume", "$", "currency"),
            (KPI_AVG_RESPONSE, "avg_response_time", "ms", "ms"),
            (KPI_HIT_RATIO, "hit_ratio", "%", "percent"),
        ]

        cards = []
        for label, key, unit, fmt in definitions:
            cur_val = current.get(key, 0)
            prev_val = previous.get(key, 0)
            delta = self._compute_delta(cur_val, prev_val)
            trend = self._determine_trend(delta, key)
            cards.append(
                MetricCard(
                    label=label,
                    value=cur_val,
                    unit=unit,
                    delta=delta,
                    delta_label="vs last week",
                    trend=trend,
                    format=fmt,
                )
            )
        return cards

    @staticmethod
    def _compute_delta(current: float, previous: float) -> float:
        """Compute percentage change between two values."""
        if previous == 0:
            return 100.0 if current > 0 else 0.0
        return round(((current - previous) / abs(previous)) * 100, 1)

    @staticmethod
    def _determine_trend(delta: float, metric_key: str) -> str:
        """Determine trend direction. For spread and response time, lower is better."""
        if delta == 0:
            return "flat"
        inverted_metrics = {"avg_spread", "avg_response_time"}
        if metric_key in inverted_metrics:
            return "down" if delta < 0 else "up"
        return "up" if delta > 0 else "down"

    def _build_trend(self, trader_id: str, today: date) -> list[WinRateTrendPoint]:
        """Build win rate trend from wallet share snapshots."""
        raw = self.repo.get_win_rate_trend(trader_id, today)
        return [WinRateTrendPoint(date=r["date"], win_rate=r["win_rate"]) for r in raw]

    def _build_scatter(self, trader_id: str) -> list[ScatterDataPoint]:
        """Build scatter plot data from rfq_trades."""
        raw = self.repo.get_scatter_data(trader_id)
        return [
            ScatterDataPoint(
                trade_id=r["trade_id"],
                spread_vs_market=r["spread_vs_market"],
                trade_outcome_score=r["trade_outcome_score"],
                notional=r["notional"],
                status=r["status"],
                security=r["security"],
                counterparty=r["counterparty"],
            )
            for r in raw
        ]
