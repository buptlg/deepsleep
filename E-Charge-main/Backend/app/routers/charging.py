from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime
from ..core.database import get_db
from ..models.models import User, ChargingRequest, ChargingPile, ChargingMode, ChargingDetail, ChargingPileStatus
from ..schemas.charging import ChargingRequestCreate, ChargingRequestResponse
from pydantic import BaseModel
from ..services.scheduling_service import SchedulingService
from ..services.billing_service import BillingService
from ..core.security import get_current_user, get_current_admin_user
from ..core.config import settings

router = APIRouter(
    tags=["charging"]
)

class ChargingPrecheckRequest(BaseModel):
    charging_mode: str
    requested_amount: float

@router.post("/requests", response_model=ChargingRequestResponse)
def create_charging_request(
    request: ChargingRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建充电请求"""
    # 只检查等候区容量（未分配充电桩的等待请求）
    waiting_area_count = db.query(ChargingRequest).filter(
        ChargingRequest.charging_mode == request.charging_mode,
        ChargingRequest.status == "waiting",
        ChargingRequest.charging_pile_id.is_(None)
    ).count()
    
    max_capacity = (settings.FAST_QUEUE_CAPACITY 
                    if request.charging_mode == ChargingMode.FAST 
                    else settings.TRICKLE_QUEUE_CAPACITY)
    
    if waiting_area_count >= max_capacity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="等候区已满，请稍后再试"
        )
    
    # 生成排队号码
    prefix = "F" if request.charging_mode == ChargingMode.FAST else "T"
    last_request = db.query(ChargingRequest).filter(
        ChargingRequest.charging_mode == request.charging_mode
    ).order_by(ChargingRequest.id.desc()).first()
    
    if last_request:
        last_number = int(last_request.queue_number[1:])
        new_number = last_number + 1
    else:
        new_number = 1
    
    queue_number = f"{prefix}{new_number}"
    
    # 创建充电请求
    db_request = ChargingRequest(
        user_id=current_user.id,
        vehicle_id=request.vehicle_id,
        queue_number=queue_number,
        charging_mode=request.charging_mode,
        requested_amount=request.requested_amount,
        status="waiting",
        created_at=datetime.now()
    )
    
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    
    # 计算前车等待数量
    waiting_count = db.query(ChargingRequest).filter(
        ChargingRequest.charging_mode == request.charging_mode,
        ChargingRequest.status == "waiting",
        ChargingRequest.created_at < db_request.created_at
    ).count()
    
    # 尝试分配充电桩
    scheduling_service = SchedulingService(db)
    assigned_pile = scheduling_service.assign_charging_pile(db_request)
    
    if assigned_pile:
        db_request.charging_pile_id = assigned_pile.id
        db_request.status = "charging"
        db_request.started_at = datetime.now()
        db.commit()
        db.refresh(db_request)
        waiting_count = 0  # 已分配充电桩，无需等待
    
    # 添加前车等待数量到响应
    setattr(db_request, "waiting_ahead", waiting_count)
    
    return db_request

@router.get("/requests", response_model=List[ChargingRequestResponse])
def get_user_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用户的充电请求列表"""
    return db.query(ChargingRequest).filter(
        ChargingRequest.user_id == current_user.id
    ).order_by(ChargingRequest.created_at.desc()).all()

@router.get("/requests/{request_id}", response_model=ChargingRequestResponse)
def get_charging_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取充电请求详情"""
    request = db.query(ChargingRequest).filter(
        ChargingRequest.id == request_id,
        ChargingRequest.user_id == current_user.id
    ).first()
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="充电请求不存在"
        )
    return request

@router.post("/requests/{request_id}/cancel")
def cancel_charging_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """取消充电请求"""
    request = db.query(ChargingRequest).filter(
        ChargingRequest.id == request_id,
        ChargingRequest.user_id == current_user.id
    ).first()
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="充电请求不存在"
        )
    
    if request.status == "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="充电已完成，无法取消"
        )
    
    if request.status == "charging":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="充电已开始，无法取消。如需停止充电，请使用结束充电功能"
        )
    
    request.status = "cancelled"
    request.completed_at = datetime.now()
    db.commit()
    
    return {"message": "充电请求已取消"}

@router.get("/queue/status")
def get_queue_status(db: Session = Depends(get_db)):
    """获取排队状态"""
    # 首先检查数据一致性，确保充电桩状态与充电请求状态一致
    # 查找所有标记为充电中但关联的充电桩已不存在的请求
    orphaned_charging_requests = db.query(ChargingRequest).filter(
        ChargingRequest.status == "charging",
        ChargingRequest.charging_pile_id.is_(None)
    ).all()
    
    # 修复这些孤立的请求
    for req in orphaned_charging_requests:
        req.status = "waiting"  # 改为等待状态
        print(f"修复孤立的充电请求 {req.queue_number}: 无关联充电桩但标记为充电中")
    
    if orphaned_charging_requests:
        db.commit()
        print(f"已修复 {len(orphaned_charging_requests)} 个孤立的充电请求")
    
    # 获取等待中请求的数量（不包括已分配充电桩的请求）
    fast_waiting_area = db.query(ChargingRequest).filter(
        ChargingRequest.charging_mode == ChargingMode.FAST,
        ChargingRequest.status == "waiting",
        ChargingRequest.charging_pile_id.is_(None)
    ).count()
    
    trickle_waiting_area = db.query(ChargingRequest).filter(
        ChargingRequest.charging_mode == ChargingMode.TRICKLE,
        ChargingRequest.status == "waiting",
        ChargingRequest.charging_pile_id.is_(None)
    ).count()
    
    # 获取已分配充电桩但仍在等待的请求数量
    fast_waiting_queue = db.query(ChargingRequest).filter(
        ChargingRequest.charging_mode == ChargingMode.FAST,
        ChargingRequest.status == "waiting",
        ChargingRequest.charging_pile_id.isnot(None)
    ).count()
    
    trickle_waiting_queue = db.query(ChargingRequest).filter(
        ChargingRequest.charging_mode == ChargingMode.TRICKLE,
        ChargingRequest.status == "waiting",
        ChargingRequest.charging_pile_id.isnot(None)
    ).count()
    
    # 计算总等待数
    fast_waiting = fast_waiting_area + fast_waiting_queue
    trickle_waiting = trickle_waiting_area + trickle_waiting_queue
    
    # 获取所有充电桩
    fast_piles = db.query(ChargingPile).filter(
        ChargingPile.charging_mode == ChargingMode.FAST
    ).all()
    
    trickle_piles = db.query(ChargingPile).filter(
        ChargingPile.charging_mode == ChargingMode.TRICKLE
    ).all()
    
    # 修复：确保每个充电桩最多只有一辆车处于充电状态
    fast_charging_count = 0
    trickle_charging_count = 0
    
    for pile in fast_piles + trickle_piles:
        charging_requests = db.query(ChargingRequest).filter(
            ChargingRequest.charging_pile_id == pile.id,
            ChargingRequest.status == "charging"
        ).order_by(ChargingRequest.created_at).all()
        
        # 如果有多个充电请求，只保留最早的一个
        if len(charging_requests) > 1:
            keep_request = charging_requests[0]
            print(f"充电桩 {pile.pile_number} (ID: {pile.id}) 发现多辆车同时充电，保留最早的请求 {keep_request.queue_number}")
            
            for req in charging_requests[1:]:
                req.status = "waiting"
                print(f"将请求 {req.queue_number} 改为等待状态")
            
            db.commit()
        
        # 统计正在充电的车辆
        if len(charging_requests) > 0:
            if pile.charging_mode == ChargingMode.FAST:
                fast_charging_count += 1
            else:
                trickle_charging_count += 1
    
    # 构建充电桩信息
    fast_pile_info = []
    for pile in fast_piles:
        # 检查该充电桩是否有正在充电的请求
        charging_request = db.query(ChargingRequest).filter(
            ChargingRequest.charging_pile_id == pile.id,
            ChargingRequest.status == "charging"
        ).first()
        
        is_charging = charging_request is not None
        
        status = pile.status
        if is_charging and status != ChargingPileStatus.OCCUPIED:
            # 更新充电桩状态以保持一致性
            pile.status = ChargingPileStatus.OCCUPIED
            db.commit()
            status = ChargingPileStatus.OCCUPIED
        elif not is_charging and status == ChargingPileStatus.OCCUPIED:
            # 如果充电桩显示为占用但没有充电请求，更新为可用状态
            pile.status = ChargingPileStatus.AVAILABLE
            db.commit()
            status = ChargingPileStatus.AVAILABLE
            
        # 添加充电桩信息和充电中的车辆信息
        current_vehicle = None
        if is_charging:
            user = db.query(User).filter(User.id == charging_request.user_id).first()
            current_vehicle = {
                "id": charging_request.id,
                "queue_number": charging_request.queue_number,
                "user_name": user.username if user else "未知用户",
                "requested_amount": charging_request.requested_amount
            }
        
        fast_pile_info.append({
            "id": pile.id,
            "number": pile.pile_number,
            "status": status.value,
            "current_vehicle": current_vehicle
        })
        
    trickle_pile_info = []
    for pile in trickle_piles:
        # 检查该充电桩是否有正在充电的请求
        charging_request = db.query(ChargingRequest).filter(
            ChargingRequest.charging_pile_id == pile.id,
            ChargingRequest.status == "charging"
        ).first()
        
        is_charging = charging_request is not None
        
        status = pile.status
        if is_charging and status != ChargingPileStatus.OCCUPIED:
            # 更新充电桩状态以保持一致性
            pile.status = ChargingPileStatus.OCCUPIED
            db.commit()
            status = ChargingPileStatus.OCCUPIED
        elif not is_charging and status == ChargingPileStatus.OCCUPIED:
            # 如果充电桩显示为占用但没有充电请求，更新为可用状态
            pile.status = ChargingPileStatus.AVAILABLE
            db.commit()
            status = ChargingPileStatus.AVAILABLE
            
        # 添加充电桩信息和充电中的车辆信息
        current_vehicle = None
        if is_charging:
            user = db.query(User).filter(User.id == charging_request.user_id).first()
            current_vehicle = {
                "id": charging_request.id,
                "queue_number": charging_request.queue_number,
                "user_name": user.username if user else "未知用户",
                "requested_amount": charging_request.requested_amount
            }
        
        trickle_pile_info.append({
            "id": pile.id,
            "number": pile.pile_number,
            "status": status.value,
            "current_vehicle": current_vehicle
        })
    
    # 打印返回的统计数据
    print("\n返回的统计数据:")
    print(f"快充等候区: {fast_waiting_area}, 快充队列: {fast_waiting_queue}, 快充中: {fast_charging_count}")
    print(f"慢充等候区: {trickle_waiting_area}, 慢充队列: {trickle_waiting_queue}, 慢充中: {trickle_charging_count}")
    
    return {
        "fast_waiting": fast_waiting,
        "trickle_waiting": trickle_waiting,
        "fast_charging": fast_charging_count,
        "trickle_charging": trickle_charging_count,
        "fast_piles": fast_pile_info,
        "trickle_piles": trickle_pile_info,
        "fast_waiting_area": fast_waiting_area,
        "trickle_waiting_area": trickle_waiting_area,
        "fast_waiting_queue": fast_waiting_queue,
        "trickle_waiting_queue": trickle_waiting_queue
    }

@router.get("/details")
def get_user_charging_details(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用户的充电详单记录"""
    # 获取用户所有充电详单
    charging_details = db.query(ChargingDetail).join(
        ChargingRequest, ChargingDetail.request_id == ChargingRequest.id
    ).filter(
        ChargingRequest.user_id == current_user.id
    ).order_by(ChargingDetail.start_time.desc()).all()
    
    return charging_details

@router.get("/statistics")
def get_user_charging_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用户的充电统计数据"""
    # 获取用户所有充电详单
    charging_details = db.query(ChargingDetail).join(
        ChargingRequest, ChargingDetail.request_id == ChargingRequest.id
    ).filter(
        ChargingRequest.user_id == current_user.id
    ).all()
    
    # 计算统计数据
    total_energy = sum(detail.charging_amount for detail in charging_details)
    total_cost = sum(detail.total_fee for detail in charging_details)
    
    # 计算本月充电次数
    now = datetime.now()
    current_month_details = [
        detail for detail in charging_details 
        if detail.start_time.month == now.month and detail.start_time.year == now.year
    ]
    charge_count = len(current_month_details)
    
    # 获取当前是否有正在充电的请求
    active_charging = db.query(ChargingRequest).filter(
        ChargingRequest.user_id == current_user.id,
        ChargingRequest.status == "charging"
    ).first()
    
    has_active_charging = active_charging is not None
    active_pile = None
    charged_amount = 0
    progress_percent = 0
    
    if has_active_charging and active_charging.charging_pile:
        pile = active_charging.charging_pile
        active_pile = pile.pile_number
        
        # 计算已充电量和进度
        if active_charging.started_at:
            time_elapsed = (datetime.now() - active_charging.started_at).total_seconds() / 3600  # 小时
            # 确保已充电量不超过请求充电量
            calculated_amount = pile.power * time_elapsed
            charged_amount = round(min(calculated_amount, active_charging.requested_amount), 2)
            progress_percent = min(round((charged_amount / active_charging.requested_amount) * 100), 100)
    
    return {
        "chargeCount": charge_count,
        "totalEnergy": round(total_energy, 2),
        "totalCost": round(total_cost, 2),
        "hasActiveCharging": has_active_charging,
        "activePile": active_pile,
        "chargedAmount": charged_amount,
        "progressPercent": progress_percent
    }

@router.post("/requests/{request_id}/finish")
def finish_charging(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """结束充电并生成充电详单"""
    # 获取充电请求
    charging_request = db.query(ChargingRequest).filter(
        ChargingRequest.id == request_id,
        ChargingRequest.user_id == current_user.id
    ).first()
    
    if not charging_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="充电请求不存在"
        )
    
    if charging_request.status != "charging":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只有正在充电的请求才能结束充电"
        )
    
    # 计算充电时间
    if not charging_request.started_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该充电请求未开始充电"
        )
    
    end_time = datetime.now()
    charging_request.completed_at = end_time
    charging_request.status = "completed"
    
    # 获取充电桩信息
    charging_pile = charging_request.charging_pile
    if not charging_pile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="充电请求未关联充电桩"
        )
    
    # 计算充电时长（小时）
    charging_duration = (end_time - charging_request.started_at).total_seconds() / 3600
    
    # 根据充电桩功率计算实际充电量
    charging_amount = min(charging_pile.power * charging_duration, charging_request.requested_amount)
    
    # 使用计费服务计算费用
    billing_service = BillingService()
    electricity_fee, service_fee, total_fee = billing_service.calculate_fee(
        charging_amount, 
        charging_request.started_at, 
        end_time
    )
    
    # 创建充电详单
    charging_detail = ChargingDetail(
        request_id=charging_request.id,
        charging_pile_id=charging_pile.id,
        start_time=charging_request.started_at,
        end_time=end_time,
        charging_amount=charging_amount,
        charging_duration=charging_duration,
        electricity_fee=electricity_fee,
        service_fee=service_fee,
        total_fee=total_fee
    )
    
    # 更新充电桩的累计充电数据
    charging_pile.total_charging_times += 1
    charging_pile.total_charging_duration += charging_duration
    charging_pile.total_charging_amount += charging_amount
    
    # 保存数据
    db.add(charging_detail)
    db.commit()
    
    # 让下一辆等待的车开始充电
    scheduling_service = SchedulingService(db)
    scheduling_service.handle_charging_completion(charging_pile)
    
    return {
        "message": "充电已完成",
        "detail_id": charging_detail.id,
        "charging_amount": round(charging_amount, 2),
        "charging_duration": round(charging_duration, 2),
        "electricity_fee": round(electricity_fee, 2),
        "service_fee": round(service_fee, 2),
        "total_fee": round(total_fee, 2)
    }

@router.get("/queue/status/current")
def get_current_queue_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前用户的排队状态"""
    # 查找当前用户最新的未完成充电请求
    request = db.query(ChargingRequest).filter(
        ChargingRequest.user_id == current_user.id,
        ChargingRequest.status.in_(["waiting", "charging"])
    ).order_by(ChargingRequest.created_at.desc()).first()
    
    # 如果没有找到请求
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="无有效排队号，请先提交充电请求"
        )
    
    # 如果充电已开始
    if request.status == "charging":
        return {
            "message": "充电已开始",
            "request_id": request.id,
            "queue_number": request.queue_number,
            "charging_mode": request.charging_mode.value,
            "status": "charging",
            "requested_amount": request.requested_amount,
            "started_at": request.started_at,
            "charging_pile_id": request.charging_pile_id
        }
    
    # 如果还在等待中，计算前方等待车辆数
    waiting_ahead = db.query(ChargingRequest).filter(
        ChargingRequest.charging_mode == request.charging_mode,
        ChargingRequest.status == "waiting",
        ChargingRequest.created_at < request.created_at
    ).count()
    
    # 判断是在等候区等候还是已进入充电区排队
    if request.charging_pile_id:
        # 已分配充电桩，说明已进入充电区排队
        waiting_status = "charging_queue"
        
        # 获取充电桩信息
        pile = db.query(ChargingPile).filter(ChargingPile.id == request.charging_pile_id).first()
        pile_name = f"{pile.pile_number}" if pile else "未知"
        pile_type = "快充桩" if (pile and pile.charging_mode == ChargingMode.FAST) else "慢充桩"
        
        status_message = f"在{pile_type} {pile_name}后排队中"
    else:
        # 未分配充电桩，说明还在等候区等候
        waiting_status = "waiting_area"
        status_message = "等候区等候中"
    
    # 计算估计等待时间
    estimated_wait_time = ""
    
    # 根据充电模式获取充电功率
    if request.charging_mode == ChargingMode.FAST:
        power = 30  # 快充功率（度/小时）
    else:
        power = 7  # 慢充功率（度/小时）
    
    # 如果已经分配了充电桩，计算更准确的等待时间
    if request.charging_pile_id:
        # 获取该充电桩当前正在充电的请求
        charging_request = db.query(ChargingRequest).filter(
            ChargingRequest.charging_pile_id == request.charging_pile_id,
            ChargingRequest.status == "charging"
        ).first()
        
        wait_time_hours = 0
        
        if charging_request and charging_request.started_at:
            # 计算当前充电请求的剩余充电时间
            elapsed_time = (datetime.now() - charging_request.started_at).total_seconds() / 3600  # 小时
            total_charging_time = charging_request.requested_amount / power  # 总充电时间
            remaining_time = max(0, total_charging_time - elapsed_time)  # 剩余时间
            wait_time_hours += remaining_time
        
        # 计算前面等待车辆的充电时间
        waiting_requests = db.query(ChargingRequest).filter(
            ChargingRequest.charging_pile_id == request.charging_pile_id,
            ChargingRequest.status == "waiting",
            ChargingRequest.created_at < request.created_at
        ).order_by(ChargingRequest.created_at).all()
        
        for wait_req in waiting_requests:
            wait_time_hours += wait_req.requested_amount / power
    else:
        # 未分配充电桩时，使用简单估计
        # 假设每个充电桩都有队列长度限制，分配时会选择最快完成的充电桩
        # 计算当前模式下正在充电的请求数，假设它们平均剩余一半的充电时间
        active_charging = db.query(ChargingRequest).filter(
            ChargingRequest.charging_mode == request.charging_mode,
            ChargingRequest.status == "charging"
        ).count()
        
        # 获取该模式下的充电桩数量
        pile_count = db.query(ChargingPile).filter(
            ChargingPile.charging_mode == request.charging_mode,
            ChargingPile.status.in_([ChargingPileStatus.AVAILABLE, ChargingPileStatus.OCCUPIED])
        ).count()
        
        if pile_count == 0:  # 防止除零错误
            pile_count = 1
            
        # 估算每个充电桩平均要处理的请求数
        avg_requests_per_pile = max(1, (waiting_ahead + active_charging) / pile_count)
        
        # 简单估算：假设等候区中每个请求平均需要充电量为10度
        avg_charging_amount = 10  # 假设的平均充电量
        # 等待时间 = 平均每个充电桩处理的请求数 * 平均充电时间
        wait_time_hours = avg_requests_per_pile * (avg_charging_amount / power)
    
    # 转换等待时间为小时和分钟的可读格式
    if wait_time_hours > 0:
        hours = int(wait_time_hours)
        minutes = int((wait_time_hours - hours) * 60)
        
        if hours > 0:
            estimated_wait_time = f"{hours}小时"
            if minutes > 0:
                estimated_wait_time += f"{minutes}分钟"
        else:
            estimated_wait_time = f"{minutes}分钟"
    
    return {
        "request_id": request.id,
        "queue_number": request.queue_number,
        "charging_mode": request.charging_mode.value,
        "status": "waiting",
        "waiting_status": waiting_status,
        "status_message": status_message,
        "waiting_ahead": waiting_ahead,
        "estimated_wait_time": estimated_wait_time,  # 新增的预计等待时间
        "requested_amount": request.requested_amount,
        "created_at": request.created_at,
        "charging_pile_id": request.charging_pile_id
    }

@router.post("/requests/precheck")
def precheck_charging_request(
    request: ChargingPrecheckRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """预检查充电请求是否可以创建，并提供当前等待状态"""
    # 转换充电模式
    charging_mode = ChargingMode.FAST if request.charging_mode == "fast" else ChargingMode.TRICKLE
    
    # 检查用户是否已有未完成的充电请求
    existing_request = db.query(ChargingRequest).filter(
        ChargingRequest.user_id == current_user.id,
        ChargingRequest.status.in_(["waiting", "charging"])
    ).first()
    
    if existing_request:
        return {
            "can_create": False,
            "status": "has_active_request",
            "message": "您已有进行中的充电请求，请先完成或取消它",
            "existing_request": {
                "id": existing_request.id,
                "queue_number": existing_request.queue_number,
                "status": existing_request.status,
                "charging_mode": existing_request.charging_mode.value
            }
        }
    
    # 只检查等候区容量（未分配充电桩的等待请求）
    waiting_area_count = db.query(ChargingRequest).filter(
        ChargingRequest.charging_mode == charging_mode,
        ChargingRequest.status == "waiting",
        ChargingRequest.charging_pile_id.is_(None)
    ).count()
    
    max_capacity = (settings.FAST_QUEUE_CAPACITY 
                    if charging_mode == ChargingMode.FAST 
                    else settings.TRICKLE_QUEUE_CAPACITY)
    
    if waiting_area_count >= max_capacity:
        return {
            "can_create": False,
            "status": "queue_full",
            "message": "等候区已满，请稍后再试",
            "queue_status": {
                "current_count": waiting_area_count,
                "max_capacity": max_capacity
            }
        }
    
    # 检查充电桩状态
    available_piles = db.query(ChargingPile).filter(
        ChargingPile.charging_mode == charging_mode,
        ChargingPile.status == ChargingPileStatus.AVAILABLE
    ).all()
    
    occupied_piles = db.query(ChargingPile).filter(
        ChargingPile.charging_mode == charging_mode,
        ChargingPile.status == ChargingPileStatus.OCCUPIED
    ).all()
    
    # 检查充电区排队情况（已分配充电桩但仍在等待的请求）
    charging_queue_count = db.query(ChargingRequest).filter(
        ChargingRequest.charging_mode == charging_mode,
        ChargingRequest.status == "waiting",
        ChargingRequest.charging_pile_id.isnot(None)
    ).count()
    
    # 检查等候区排队情况（未分配充电桩的等待请求）
    waiting_area_count = db.query(ChargingRequest).filter(
        ChargingRequest.charging_mode == charging_mode,
        ChargingRequest.status == "waiting",
        ChargingRequest.charging_pile_id.is_(None)
    ).count()
    
    # 分析可能的状态
    if len(available_piles) > 0 and waiting_area_count == 0 and charging_queue_count == 0:
        # 有空闲充电桩且无等待车辆，可以直接充电
        status = "direct_charging"
        message = "当前有空闲充电桩，提交后可直接开始充电"
        estimated_wait = "0分钟"
    elif waiting_area_count == 0 and charging_queue_count < settings.CHARGING_QUEUE_LEN * len(occupied_piles):
        # 无等候区等待，可进入充电区排队
        status = "charging_queue"
        message = "当前充电桩已满，但可进入充电区排队"
        
        # 计算预计等待时间
        power = 30 if charging_mode == ChargingMode.FAST else 7  # 充电功率
        avg_wait_time = 0
        
        # 简单估算：假设平均每个请求的充电量为10度，所需时间 = 充电量/功率
        charging_requests = db.query(ChargingRequest).filter(
            ChargingRequest.status == "charging",
            ChargingRequest.charging_mode == charging_mode
        ).all()
        
        if charging_requests:
            # 计算正在充电的车辆平均剩余时间
            total_remaining = 0
            for req in charging_requests:
                if req.started_at:
                    elapsed_time = (datetime.now() - req.started_at).total_seconds() / 3600  # 小时
                    total_time = req.requested_amount / power
                    remaining = max(0, total_time - elapsed_time)
                    total_remaining += remaining
            
            avg_wait_time = (total_remaining / len(charging_requests) + 
                             charging_queue_count * request.requested_amount / power / len(occupied_piles))
            
            # 转换为分钟
            wait_minutes = int(avg_wait_time * 60)
            estimated_wait = f"{wait_minutes}分钟"
        else:
            estimated_wait = "未知"
    else:
        # 需要进入等候区等待
        status = "waiting_area"
        message = "需要进入等候区等待"
        
        # 估算等待时间（更复杂，考虑等候区和充电区的等待）
        power = 30 if charging_mode == ChargingMode.FAST else 7
        pile_count = len(available_piles) + len(occupied_piles)
        if pile_count == 0:
            estimated_wait = "无法估计（无可用充电桩）"
        else:
            # 简单估算：每辆车平均10度电，等待时间 = 前面车辆数 * 平均充电时间 / 充电桩数量
            avg_charge = 10  # 平均充电量
            wait_time = (waiting_area_count * avg_charge / power) / pile_count
            wait_minutes = int(wait_time * 60)
            estimated_wait = f"{wait_minutes}分钟"
    
    return {
        "can_create": True,
        "status": status,
        "message": message,
        "queue_status": {
            "current_count": waiting_area_count,
            "max_capacity": max_capacity,
            "available_piles": len(available_piles),
            "occupied_piles": len(occupied_piles),
            "charging_queue_count": charging_queue_count,
            "waiting_area_count": waiting_area_count
        },
        "estimated_wait": estimated_wait
    }

@router.get("/piles")
def get_piles_info(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取充电桩信息（允许普通用户访问）"""
    piles = db.query(ChargingPile).all()
    return piles

@router.get("/admin/waiting-vehicles", response_model=List[Dict[str, Any]])
def get_waiting_vehicles(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    """管理员获取等候车辆信息"""
    # 查询等候区和充电桩队列中等待的车辆
    waiting_requests = db.query(ChargingRequest).filter(
        ChargingRequest.status.in_(["waiting"])
    ).order_by(ChargingRequest.created_at.asc()).all()
    
    charging_requests = db.query(ChargingRequest).filter(
        ChargingRequest.status == "charging"
    ).order_by(ChargingRequest.started_at.asc()).all()
    
    if not waiting_requests and not charging_requests:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="当前无等候车辆"
        )
    
    # 构建等候车辆信息列表
    waiting_vehicles = []
    
    # 添加等候区中的车辆
    for request in waiting_requests:
        user = db.query(User).filter(User.id == request.user_id).first()
        waiting_vehicles.append({
            "queue_number": request.queue_number,
            "user_id": request.user_id,
            "user_name": user.username if user else "未知用户",
            "vehicle_id": request.vehicle_id,
            "charging_mode": request.charging_mode,
            "requested_amount": request.requested_amount,
            "created_at": request.created_at,
            "status": "等候区等待中",
            "waiting_time": (datetime.now() - request.created_at).total_seconds() / 60  # 等待时间（分钟）
        })
    
    # 添加充电桩队列中等待充电的车辆
    for request in charging_requests:
        if request.charging_pile:
            pile = request.charging_pile
            user = db.query(User).filter(User.id == request.user_id).first()
            
            # 计算已充电量
            time_elapsed = (datetime.now() - request.started_at).total_seconds() / 3600  # 小时
            # 确保已充电量不超过请求充电量
            calculated_amount = pile.power * time_elapsed
            charged_amount = round(min(calculated_amount, request.requested_amount), 2)
            progress_percent = min(round((charged_amount / request.requested_amount) * 100), 100)
            
            waiting_vehicles.append({
                "queue_number": request.queue_number,
                "user_id": request.user_id,
                "user_name": user.username if user else "未知用户",
                "vehicle_id": request.vehicle_id,
                "charging_mode": request.charging_mode,
                "requested_amount": request.requested_amount,
                "charged_amount": charged_amount,
                "progress_percent": progress_percent,
                "charging_pile": pile.pile_number,
                "started_at": request.started_at,
                "status": "充电中",
                "charging_time": (datetime.now() - request.started_at).total_seconds() / 60  # 充电时间（分钟）
            })
    
    return waiting_vehicles

@router.get("/user/charging-notification")
def get_charging_notification(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    检查用户是否有可用的充电桩并可以开始充电
    返回格式:
    {
        "has_available_pile": true/false,
        "request_id": 123,
        "pile_info": {
            "pile_number": "F1",
            "pile_type": "fast/trickle"
        }
    }
    """
    # 查找用户当前在充电区排队的请求（已分配充电桩但状态仍为waiting）
    waiting_request = db.query(ChargingRequest).filter(
        ChargingRequest.user_id == current_user.id,
        ChargingRequest.status == "waiting",
        ChargingRequest.charging_pile_id.isnot(None)
    ).first()
    
    if not waiting_request:
        return {
            "has_available_pile": False,
            "message": "您没有在充电区排队的请求"
        }
    
    # 获取分配的充电桩
    charging_pile = db.query(ChargingPile).filter(
        ChargingPile.id == waiting_request.charging_pile_id
    ).first()
    
    if not charging_pile:
        return {
            "has_available_pile": False,
            "message": "未找到分配的充电桩"
        }
    
    # 检查充电桩是否可用
    if charging_pile.status == ChargingPileStatus.AVAILABLE:
        # 充电桩可用，可以通知用户
        return {
            "has_available_pile": True,
            "request_id": waiting_request.id,
            "pile_info": {
                "pile_id": charging_pile.id,
                "pile_number": charging_pile.pile_number,
                "pile_type": charging_pile.charging_mode.value
            },
            "message": f"您分配的充电桩 {charging_pile.pile_number} 已可用，请前往充电"
        }
    else:
        # 充电桩还在使用中
        return {
            "has_available_pile": False,
            "message": "您分配的充电桩还在使用中，请耐心等待"
        }

@router.post("/requests/{request_id}/start-charging")
def start_charging(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    用户确认开始充电，更新请求状态为charging
    """
    # 获取充电请求
    charging_request = db.query(ChargingRequest).filter(
        ChargingRequest.id == request_id,
        ChargingRequest.user_id == current_user.id
    ).first()
    
    if not charging_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="充电请求不存在"
        )
    
    if charging_request.status != "waiting":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只有等待状态的请求才能开始充电"
        )
    
    if not charging_request.charging_pile_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该充电请求未分配充电桩"
        )
    
    # 获取充电桩
    charging_pile = db.query(ChargingPile).filter(
        ChargingPile.id == charging_request.charging_pile_id
    ).first()
    
    if not charging_pile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="未找到分配的充电桩"
        )
    
    # 检查充电桩是否可用
    if charging_pile.status != ChargingPileStatus.AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该充电桩当前不可用，请稍后再试"
        )
    
    # 更新充电请求状态
    charging_request.status = "charging"
    charging_request.started_at = datetime.now()
    
    # 更新充电桩状态
    charging_pile.status = ChargingPileStatus.OCCUPIED
    
    # 提交事务
    db.commit()
    
    return {
        "message": "充电已开始",
        "request_id": charging_request.id,
        "pile_number": charging_pile.pile_number,
        "started_at": charging_request.started_at
    } 