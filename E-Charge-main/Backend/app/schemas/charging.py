from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from ..models.models import ChargingMode

class ChargingRequestBase(BaseModel):
    vehicle_id: int
    charging_mode: ChargingMode
    requested_amount: float

class ChargingRequestCreate(ChargingRequestBase):
    pass

class ChargingRequestResponse(ChargingRequestBase):
    id: int
    user_id: int
    queue_number: str
    status: str
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    charging_pile_id: Optional[int]
    waiting_ahead: Optional[int] = 0  # 前车等待数量

    class Config:
        from_attributes = True

class ChargingDetailResponse(BaseModel):
    id: int
    request_id: int
    charging_pile_id: int
    start_time: datetime
    end_time: datetime
    charging_amount: float
    charging_duration: float
    electricity_fee: float
    service_fee: float
    total_fee: float

    class Config:
        from_attributes = True 