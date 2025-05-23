from sqlalchemy.orm import Session
from datetime import datetime
from ..models.models import ChargingRequest, ChargingDetail
from ..schemas.charging import ChargingRequestCreate
from .scheduling_service import get_available_charging_pile

def create_charging_request(db: Session, request: ChargingRequestCreate, user_id: int):
    # 获取可用的充电桩
    charging_pile = get_available_charging_pile(db, request.charging_mode)
    if not charging_pile:
        # 如果没有可用充电桩，将请求加入队列
        queue_number = get_next_queue_number(db)
        db_request = ChargingRequest(
            user_id=user_id,
            vehicle_id=request.vehicle_id,
            charging_mode=request.charging_mode,
            requested_amount=request.requested_amount,
            status="queued",
            queue_number=queue_number
        )
    else:
        # 如果有可用充电桩，直接分配
        db_request = ChargingRequest(
            user_id=user_id,
            vehicle_id=request.vehicle_id,
            charging_mode=request.charging_mode,
            requested_amount=request.requested_amount,
            status="charging",
            charging_pile_id=charging_pile.id,
            started_at=datetime.utcnow()
        )
    
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    return db_request

def get_next_queue_number(db: Session) -> int:
    # 获取当前最大队列号
    max_queue = db.query(ChargingRequest.queue_number).order_by(
        ChargingRequest.queue_number.desc()
    ).first()
    return (max_queue[0] + 1) if max_queue else 1

def get_user_requests(db: Session, user_id: int):
    return db.query(ChargingRequest).filter(
        ChargingRequest.user_id == user_id
    ).order_by(ChargingRequest.created_at.desc()).all()

def get_request_details(db: Session, request_id: int):
    return db.query(ChargingDetail).filter(
        ChargingDetail.request_id == request_id
    ).first()

def cancel_charging_request(db: Session, request_id: int, user_id: int):
    request = db.query(ChargingRequest).filter(
        ChargingRequest.id == request_id,
        ChargingRequest.user_id == user_id
    ).first()
    
    if not request:
        return None
        
    if request.status in ["completed", "cancelled"]:
        return None
        
    request.status = "cancelled"
    request.completed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(request)
    return request 