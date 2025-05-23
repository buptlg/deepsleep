from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime, timedelta
from ..core.database import get_db
from ..models.models import User, ChargingPile, ChargingRequest, ChargingDetail, ChargingPileStatus as PileStatus
from ..schemas.admin import ChargingPileStatus, ChargingPileResponse, ReportResponse
from ..core.security import get_current_admin_user

router = APIRouter(
    tags=["admin"]
)

def get_status_text(status):
    """将充电桩状态转换为用户友好的文本描述"""
    if status == PileStatus.AVAILABLE:
        return "空闲可用"
    elif status == PileStatus.OCCUPIED:
        return "正在使用"
    elif status == PileStatus.FAULT:
        return "故障"
    elif status == PileStatus.MAINTENANCE:
        return "维护中"
    elif status == PileStatus.CLOSED:
        return "已关闭"
    else:
        return "未知状态"

@router.put("/piles/{pile_id}/status")
def update_pile_status(
    pile_id: int,
    status: ChargingPileStatus,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """更新充电桩状态"""
    pile = db.query(ChargingPile).filter(ChargingPile.id == pile_id).first()
    if not pile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="充电桩不存在"
        )
    
    pile.status = status
    db.commit()
    
    return {"message": "充电桩状态已更新"}

@router.get("/piles", response_model=List[ChargingPileResponse])
def get_all_piles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """获取所有充电桩状态"""
    return db.query(ChargingPile).all()

@router.get("/piles/{pile_id}/queue")
def get_pile_queue(
    pile_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """获取充电桩排队信息"""
    # 获取正在充电的车辆
    charging_requests = db.query(ChargingRequest).filter(
        ChargingRequest.charging_pile_id == pile_id,
        ChargingRequest.status == "charging"
    ).all()
    
    # 获取正在等待的车辆
    waiting_requests = db.query(ChargingRequest).filter(
        ChargingRequest.charging_pile_id == pile_id,
        ChargingRequest.status == "waiting"
    ).order_by(ChargingRequest.created_at).all()
    
    result = []
    
    # 处理充电中的车辆
    for req in charging_requests:
        user = db.query(User).filter(User.id == req.user_id).first()
        # 计算已充电量和进度
        charged_amount = 0
        progress_percent = 0
        if req.started_at:
            pile = req.charging_pile
            time_elapsed = (datetime.now() - req.started_at).total_seconds() / 3600  # 小时
            # 确保已充电量不超过请求充电量
            calculated_amount = pile.power * time_elapsed
            charged_amount = round(min(calculated_amount, req.requested_amount), 2)
            progress_percent = min(round((charged_amount / req.requested_amount) * 100), 100)
            
        result.append({
            "id": req.id,
            "user_id": req.user_id,
            "user_name": user.username if user else "未知用户",
            "battery_capacity": req.vehicle.battery_capacity if req.vehicle else 0,
            "requested_amount": req.requested_amount,
            "charged_amount": charged_amount,
            "progress_percent": progress_percent,
            "waiting_time": (datetime.now() - req.created_at).total_seconds() / 3600,
            "charging_time": (datetime.now() - req.started_at).total_seconds() / 3600 if req.started_at else 0,
            "status": "charging",  # 明确标记为charging状态
            "status_text": "正在充电",
            "is_charging": True,  # 明确标记为正在充电
            "queue_number": req.queue_number,
            "started_at": req.started_at
        })
    
    # 处理等待中的车辆
    for req in waiting_requests:
        user = db.query(User).filter(User.id == req.user_id).first()
        result.append({
            "id": req.id,
            "user_id": req.user_id,
            "user_name": user.username if user else "未知用户",
            "battery_capacity": req.vehicle.battery_capacity if req.vehicle else 0,
            "requested_amount": req.requested_amount,
            "waiting_time": (datetime.now() - req.created_at).total_seconds() / 3600,
            "status": "waiting",  # 明确标记为waiting状态
            "status_text": "充电区排队中",
            "is_charging": False,  # 明确标记为非充电状态
            "queue_number": req.queue_number
        })
    
    return result

@router.get("/report", response_model=ReportResponse)
def get_report(
    start_date: datetime,
    end_date: datetime,
    pile_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """获取报表数据"""
    print(f"报表API调用 - 开始时间: {start_date}, 结束时间: {end_date}, 充电桩ID: {pile_id}")
    
    # 构建查询条件
    query = db.query(ChargingDetail).filter(
        ChargingDetail.start_time >= start_date,
        ChargingDetail.end_time <= end_date
    )
    
    # 如果指定了充电桩ID，添加过滤条件
    if pile_id is not None:
        query = query.filter(ChargingDetail.charging_pile_id == pile_id)
        print(f"过滤特定充电桩: {pile_id}")
    
    details = query.all()
    print(f"查询到 {len(details)} 条充电详单记录")
    
    # 如果没有数据，返回空的统计结果
    if not details:
        print("没有找到充电详单数据")
        return {
            "start_date": start_date,
            "end_date": end_date,
            "pile_statistics": {}
        }
    
    # 按充电桩分组统计
    pile_stats = {}
    for detail in details:
        pile_id_key = detail.charging_pile_id
        if pile_id_key not in pile_stats:
            pile_stats[pile_id_key] = {
                "charging_times": 0,
                "total_duration": 0.0,
                "total_amount": 0.0,
                "total_electricity_fee": 0.0,
                "total_service_fee": 0.0,
                "total_fee": 0.0
            }
        
        stats = pile_stats[pile_id_key]
        stats["charging_times"] += 1
        stats["total_duration"] += float(detail.charging_duration or 0)
        stats["total_amount"] += float(detail.charging_amount or 0)
        stats["total_electricity_fee"] += float(detail.electricity_fee or 0)
        stats["total_service_fee"] += float(detail.service_fee or 0)
        stats["total_fee"] += float(detail.total_fee or 0)
    
    print(f"统计结果: {pile_stats}")
    
    # 确保所有充电桩都有统计数据（即使为0）
    if pile_id is None:
        # 获取所有充电桩
        all_piles = db.query(ChargingPile).all()
        for pile in all_piles:
            if pile.id not in pile_stats:
                pile_stats[pile.id] = {
                    "charging_times": 0,
                    "total_duration": 0.0,
                    "total_amount": 0.0,
                    "total_electricity_fee": 0.0,
                    "total_service_fee": 0.0,
                    "total_fee": 0.0
                }
    elif pile_id is not None and pile_id not in pile_stats:
        # 如果指定的充电桩没有数据，也要返回0值统计
        pile_stats[pile_id] = {
            "charging_times": 0,
            "total_duration": 0.0,
            "total_amount": 0.0,
            "total_electricity_fee": 0.0,
            "total_service_fee": 0.0,
            "total_fee": 0.0
        }
    
    return {
        "start_date": start_date,
        "end_date": end_date,
        "pile_statistics": pile_stats
    }

@router.get("/statistics")
def get_admin_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """获取管理员仪表盘统计数据"""
    # 获取所有充电桩
    charging_piles = db.query(ChargingPile).all()
    
    # 计算运行中的充电桩数量（排除故障、维护和已关闭的充电桩）
    active_piles = sum(1 for pile in charging_piles if pile.status in [PileStatus.AVAILABLE, PileStatus.OCCUPIED])
    total_piles = len(charging_piles)
    
    # 获取排队车辆总数
    queued_cars = db.query(ChargingRequest).filter(
        ChargingRequest.status == "waiting"
    ).count()
    
    # 计算今日总收入
    today = datetime.now().date()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())
    
    today_details = db.query(ChargingDetail).filter(
        ChargingDetail.start_time >= today_start,
        ChargingDetail.end_time <= today_end
    ).all()
    
    total_revenue = sum(detail.total_fee for detail in today_details)
    
    # 获取充电桩详细信息
    pile_details = []
    for pile in charging_piles:
        # 获取与该充电桩相关的所有充电详单
        details = db.query(ChargingDetail).filter(
            ChargingDetail.charging_pile_id == pile.id
        ).all()
        
        # 计算总充电次数、时长和充电量
        total_charges = len(details)
        total_hours = sum(detail.charging_duration for detail in details)
        total_energy = sum(detail.charging_amount for detail in details)
        
        # 获取该充电桩的排队车辆数量
        queue_count = db.query(ChargingRequest).filter(
            ChargingRequest.charging_pile_id == pile.id,
            ChargingRequest.status == "waiting"
        ).count()
        
        # 检查充电桩是否有正在充电的请求
        is_occupied = db.query(ChargingRequest).filter(
            ChargingRequest.charging_pile_id == pile.id,
            ChargingRequest.status == "charging"
        ).first() is not None
        
        # 确定充电桩的实际状态
        actual_status = pile.status
        if is_occupied and pile.status == PileStatus.AVAILABLE:
            actual_status = PileStatus.OCCUPIED
        
        pile_details.append({
            "id": pile.id,
            "name": f"{'快充桩' if pile.charging_mode.value == 'fast' else '慢充桩'} {pile.pile_number}",
            "isActive": actual_status in [PileStatus.AVAILABLE, PileStatus.OCCUPIED],
            "isOccupied": actual_status == PileStatus.OCCUPIED,
            "statusText": get_status_text(actual_status),
            "totalCharges": total_charges,
            "totalHours": round(total_hours, 2),
            "totalEnergy": round(total_energy, 2),
            "queueCount": queue_count
        })
    
    # 获取等待车辆信息
    waiting_cars = []
    queued_requests = db.query(ChargingRequest).filter(
        ChargingRequest.status == "waiting"
    ).order_by(ChargingRequest.created_at).all()
    
    for req in queued_requests:
        # 计算等待时间
        wait_time = datetime.now() - req.created_at
        hours, remainder = divmod(wait_time.total_seconds(), 3600)
        minutes, _ = divmod(remainder, 60)
        
        queue_time = ""
        if hours > 0:
            queue_time += f"{int(hours)}小时"
        if minutes > 0 or hours == 0:
            queue_time += f"{int(minutes)}分钟"
        
        # 获取充电桩名称
        pile_name = "未分配"
        if req.charging_pile_id:
            pile = db.query(ChargingPile).filter(ChargingPile.id == req.charging_pile_id).first()
            if pile:
                pile_name = f"{'快充桩' if pile.charging_mode.value == 'fast' else '慢充桩'} {pile.pile_number}"
        
        # 获取用户的车辆电池容量
        battery_capacity = 0
        if req.vehicle:
            battery_capacity = req.vehicle.battery_capacity
        
        waiting_cars.append({
            "id": req.id,
            "pileName": pile_name,
            "userId": db.query(User).filter(User.id == req.user_id).first().username,
            "batteryCapacity": battery_capacity,
            "requestedCharge": req.requested_amount,
            "queueTime": queue_time,
            "status": "排队中",
            "statusClass": "waiting"
        })
    
    return {
        "activePiles": active_piles,
        "totalPiles": total_piles,
        "totalQueuedCars": queued_cars,
        "totalRevenue": round(total_revenue, 2),
        "chargingPiles": pile_details,
        "waitingCars": waiting_cars
    }

@router.post("/piles/{pile_id}/start")
def start_charging_pile(
    pile_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """启动充电桩"""
    # 查找充电桩
    pile = db.query(ChargingPile).filter(ChargingPile.id == pile_id).first()
    if not pile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="充电桩不存在"
        )
    
    # 检查充电桩状态
    if pile.status == PileStatus.AVAILABLE or pile.status == PileStatus.OCCUPIED:
        # 充电桩已经是工作状态
        return {
            "message": "充电桩已处于工作状态",
            "status": pile.status.value
        }
    
    # 将充电桩状态更新为可用
    pile.status = PileStatus.AVAILABLE
    db.commit()
    
    return {
        "message": "充电桩启动成功",
        "status": PileStatus.AVAILABLE.value
    }

@router.get("/piles/{pile_id}")
def get_pile_detail(
    pile_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """获取单个充电桩的详细信息"""
    pile = db.query(ChargingPile).filter(ChargingPile.id == pile_id).first()
    if not pile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="充电桩不存在"
        )
    
    # 获取该充电桩的所有充电详情记录
    details = db.query(ChargingDetail).filter(
        ChargingDetail.charging_pile_id == pile_id
    ).all()
    
    # 获取当前排队的车辆数
    queue_count = db.query(ChargingRequest).filter(
        ChargingRequest.charging_pile_id == pile_id,
        ChargingRequest.status.in_(["waiting", "charging"])
    ).count()
    
    # 获取正在充电的车辆信息
    charging_vehicle = db.query(ChargingRequest).filter(
        ChargingRequest.charging_pile_id == pile_id,
        ChargingRequest.status == "charging"
    ).first()
    
    current_charging = None
    if charging_vehicle:
        user = db.query(User).filter(User.id == charging_vehicle.user_id).first()
        
        # 计算已充电量和进度
        charged_amount = 0
        progress_percent = 0
        if charging_vehicle.started_at:
            time_elapsed = (datetime.now() - charging_vehicle.started_at).total_seconds() / 3600  # 小时
            # 确保已充电量不超过请求充电量
            calculated_amount = pile.power * time_elapsed
            charged_amount = round(min(calculated_amount, charging_vehicle.requested_amount), 2)
            progress_percent = min(round((charged_amount / charging_vehicle.requested_amount) * 100), 100)
        
        current_charging = {
            "id": charging_vehicle.id,
            "user_id": charging_vehicle.user_id,
            "user_name": user.username if user else "未知用户",
            "battery_capacity": charging_vehicle.vehicle.battery_capacity if charging_vehicle.vehicle else 0,
            "requested_amount": charging_vehicle.requested_amount,
            "charged_amount": charged_amount,
            "progress_percent": progress_percent,
            "charging_time": (datetime.now() - charging_vehicle.started_at).total_seconds() / 3600 if charging_vehicle.started_at else 0,
            "queue_number": charging_vehicle.queue_number,
            "started_at": charging_vehicle.started_at
        }
    
    # 计算累计数据
    total_charges = len(details)
    total_hours = sum(detail.charging_duration for detail in details)
    total_energy = sum(detail.charging_amount for detail in details)
    total_revenue = sum(detail.total_fee for detail in details)
    
    # 添加额外计算信息到返回结果
    return {
        "id": pile.id,
        "pile_number": pile.pile_number,
        "charging_mode": pile.charging_mode,
        "status": pile.status,
        "power": pile.power,
        "total_charging_times": total_charges,
        "total_charging_duration": round(total_hours, 2),
        "total_charging_amount": round(total_energy, 2),
        "total_revenue": round(total_revenue, 2),
        "queue_count": queue_count,
        "current_charging": current_charging  # 添加当前正在充电的车辆信息
    }

@router.post("/piles/{pile_id}/toggle")
def toggle_pile_status(
    pile_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """切换充电桩状态（启用/停用）"""
    pile = db.query(ChargingPile).filter(ChargingPile.id == pile_id).first()
    if not pile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="充电桩不存在"
        )
    
    # 切换状态
    if pile.status == PileStatus.AVAILABLE or pile.status == PileStatus.OCCUPIED:
        # 如果正在使用中，不允许直接关闭
        if pile.status == PileStatus.OCCUPIED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="充电桩正在使用中，无法直接关闭"
            )
        pile.status = PileStatus.CLOSED
        message = "充电桩已关闭"
    else:
        pile.status = PileStatus.AVAILABLE
        message = "充电桩已启用"
    
    db.commit()
    
    return {
        "message": message,
        "status": pile.status.value
    }

@router.get("/waiting-area")
def get_waiting_area(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """获取等候区等待的车辆信息（尚未分配充电桩的请求）"""
    # 获取等候区等待的车辆（未分配充电桩）
    waiting_requests = db.query(ChargingRequest).filter(
        ChargingRequest.status == "waiting",
        ChargingRequest.charging_pile_id == None
    ).order_by(ChargingRequest.created_at).all()
    
    result = []
    
    # 处理等候区等待的车辆
    for req in waiting_requests:
        result.append({
            "id": req.id,
            "user_id": req.user_id,
            "user_name": db.query(User).filter(User.id == req.user_id).first().username if db.query(User).filter(User.id == req.user_id).first() else "未知用户",
            "battery_capacity": req.vehicle.battery_capacity if req.vehicle else 0,
            "requested_amount": req.requested_amount,
            "charging_mode": req.charging_mode.value,
            "waiting_time": (datetime.now() - req.created_at).total_seconds() / 3600,
            "status": "等候区等候中",
            "queue_number": req.queue_number,
            "created_at": req.created_at
        })
    
    return result 