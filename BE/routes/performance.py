"""Performance overview endpoint — GET /performance."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from BE.models.db import get_db
from BE.models.schemas import PerformanceResponse
from BE.services.dependencies import get_performance_service
from BE.utils.exceptions import InvalidParamsException

router = APIRouter(tags=["Performance"])


@router.get("/performance", response_model=PerformanceResponse)
def get_performance(
    trader_id: str = Query(..., description="Trader identifier from users table"),
    db: Session = Depends(get_db),
) -> PerformanceResponse:
    """Fetch KPI cards, win rate trend, and spread vs market scatter data."""
    if not trader_id or not trader_id.strip():
        raise InvalidParamsException("trader_id is required")

    service = get_performance_service(db)
    return service.get_performance(trader_id)
