from pydantic import BaseModel
from datetime import datetime
from typing import Dict
from ..models.models import ChargingPileStatus

class ChargingPileResponse(BaseModel):
    id: int
    pile_number: str
    charging_mode: str
    status: ChargingPileStatus
    power: float
    total_charging_times: int
    total_charging_duration: float
    total_charging_amount: float

    class Config:
        from_attributes = True

class PileStatistics(BaseModel):
    charging_times: int
    total_duration: float
    total_amount: float
    total_electricity_fee: float
    total_service_fee: float
    total_fee: float

class ReportResponse(BaseModel):
    start_date: datetime
    end_date: datetime
    pile_statistics: Dict[int, PileStatistics] 