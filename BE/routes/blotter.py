"""Trade blotter endpoint — POST /trade-blotter."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from BE.models.db import get_db
from BE.models.schemas import TradeBlotterRequest, TradeBlotterResponse
from BE.services.dependencies import get_blotter_service
from BE.utils.exceptions import InvalidParamsException

router = APIRouter(tags=["Trade Blotter"])

_VALID_STATUSES = {"WON", "LOST", "PENDING", "CANCELLED"}
_VALID_ASSET_CLASSES = {"IG_CORP", "HY_CORP", "GOVT", "MBS", "ABS"}


@router.post("/trade-blotter", response_model=TradeBlotterResponse)
def search_trade_blotter(
    request: TradeBlotterRequest,
    db: Session = Depends(get_db),
) -> TradeBlotterResponse:
    """Search and filter the trade blotter."""
    if not request.trader_id or not request.trader_id.strip():
        raise InvalidParamsException("trader_id is required")

    if request.filters:
        if request.filters.status:
            invalid = set(request.filters.status) - _VALID_STATUSES
            if invalid:
                raise InvalidParamsException(
                    f"Invalid status filter values: {invalid}. Valid values: {_VALID_STATUSES}"
                )
        if request.filters.asset_class:
            invalid = set(request.filters.asset_class) - _VALID_ASSET_CLASSES
            if invalid:
                raise InvalidParamsException(
                    f"Invalid asset_class filter values: {invalid}. Valid values: {_VALID_ASSET_CLASSES}"
                )

    service = get_blotter_service(db)
    return service.search_blotter(request)
