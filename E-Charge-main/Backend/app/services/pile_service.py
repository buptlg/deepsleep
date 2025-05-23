from sqlalchemy.orm import Session
from datetime import datetime
from ..models.models import ChargingPile, ChargingRequest
from ..schemas.admin import ChargingPileStatus

def get_all_piles(db: Session):
    return db.query(ChargingPile).all()

def get_pile_by_id(db: Session, pile_id: int):
    return db.query(ChargingPile).filter(ChargingPile.id == pile_id).first()

def update_pile_status(db: Session, pile_id: int, status: ChargingPileStatus):
    pile = get_pile_by_id(db, pile_id)
    if not pile:
        return None
        
    pile.status = status
    db.commit()
    db.refresh(pile)
    return pile

def get_pile_queue(db: Session, pile_id: int):
    return db.query(ChargingRequest).filter(
        ChargingRequest.charging_pile_id == pile_id,
        ChargingRequest.status == "charging"
    ).all()

def get_pile_statistics(db: Session, pile_id: int, start_date: datetime, end_date: datetime):
    requests = db.query(ChargingRequest).filter(
        ChargingRequest.charging_pile_id == pile_id,
        ChargingRequest.started_at >= start_date,
        ChargingRequest.completed_at <= end_date,
        ChargingRequest.status == "completed"
    ).all()
    
    stats = {
        "charging_times": len(requests),
        "total_duration": sum((req.completed_at - req.started_at).total_seconds() / 3600 for req in requests),
        "total_amount": sum(req.charging_detail.charging_amount for req in requests if req.charging_detail),
        "total_electricity_fee": sum(req.charging_detail.electricity_fee for req in requests if req.charging_detail),
        "total_service_fee": sum(req.charging_detail.service_fee for req in requests if req.charging_detail),
        "total_fee": sum(req.charging_detail.total_fee for req in requests if req.charging_detail)
    }
    
    return stats 