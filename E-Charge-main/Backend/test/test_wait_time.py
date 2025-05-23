#!/usr/bin/env python3
from app.core.database import SessionLocal
from app.models.models import ChargingRequest, ChargingMode, ChargingPile, ChargingPileStatus
from datetime import datetime
from sqlalchemy.orm import Session

def estimate_wait_time(db: Session, request_id: int) -> str:
    """估算特定充电请求的等待时间"""
    # 获取请求信息
    request = db.query(ChargingRequest).filter(ChargingRequest.id == request_id).first()
    if not request:
        return "请求不存在"
    
    if request.status == "charging":
        return "该请求已经在充电中"
    
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
            print(f"当前充电请求 {charging_request.queue_number} 剩余时间: {remaining_time:.2f}小时")
        
        # 计算前面等待车辆的充电时间
        waiting_requests = db.query(ChargingRequest).filter(
            ChargingRequest.charging_pile_id == request.charging_pile_id,
            ChargingRequest.status == "waiting",
            ChargingRequest.created_at < request.created_at
        ).order_by(ChargingRequest.created_at).all()
        
        for wait_req in waiting_requests:
            charge_time = wait_req.requested_amount / power
            wait_time_hours += charge_time
            print(f"等待的请求 {wait_req.queue_number} 预计充电时间: {charge_time:.2f}小时")
    else:
        # 未分配充电桩时，使用简单估计
        # 计算当前模式下正在充电的请求数
        active_charging = db.query(ChargingRequest).filter(
            ChargingRequest.charging_mode == request.charging_mode,
            ChargingRequest.status == "charging"
        ).count()
        
        # 获取该模式下的充电桩数量
        pile_count = db.query(ChargingPile).filter(
            ChargingPile.charging_mode == request.charging_mode,
            ChargingPile.status.in_([ChargingPileStatus.AVAILABLE, ChargingPileStatus.OCCUPIED])
        ).count()
        
        # 计算前方等待车辆数
        waiting_ahead = db.query(ChargingRequest).filter(
            ChargingRequest.charging_mode == request.charging_mode,
            ChargingRequest.status == "waiting",
            ChargingRequest.created_at < request.created_at
        ).count()
        
        if pile_count == 0:  # 防止除零错误
            pile_count = 1
            
        # 估算每个充电桩平均要处理的请求数
        avg_requests_per_pile = max(1, (waiting_ahead + active_charging) / pile_count)
        
        # 简单估算：假设等候区中每个请求平均需要充电量为10度
        avg_charging_amount = 10  # 假设的平均充电量
        wait_time_hours = avg_requests_per_pile * (avg_charging_amount / power)
        
        print(f"等候区估算 - 前方等待车辆: {waiting_ahead}, 充电中: {active_charging}, 充电桩数: {pile_count}")
        print(f"平均每个充电桩处理请求数: {avg_requests_per_pile:.2f}")
    
    # 转换等待时间为小时和分钟的可读格式
    hours = int(wait_time_hours)
    minutes = int((wait_time_hours - hours) * 60)
    
    estimated_wait_time = ""
    if hours > 0:
        estimated_wait_time = f"{hours}小时"
        if minutes > 0:
            estimated_wait_time += f"{minutes}分钟"
    else:
        estimated_wait_time = f"{minutes}分钟"
    
    return f"预计等待时间: {estimated_wait_time} (约 {wait_time_hours:.2f} 小时)"

def main():
    db = SessionLocal()
    try:
        # 获取所有等待状态的请求
        waiting_requests = db.query(ChargingRequest).filter(
            ChargingRequest.status == "waiting"
        ).order_by(ChargingRequest.created_at).all()
        
        if not waiting_requests:
            print("当前没有等待中的充电请求")
            return
        
        print(f"共找到 {len(waiting_requests)} 个等待中的充电请求")
        
        for request in waiting_requests:
            print("\n" + "="*50)
            print(f"请求ID: {request.id}, 排队号: {request.queue_number}")
            print(f"充电模式: {'快充' if request.charging_mode == ChargingMode.FAST else '慢充'}")
            print(f"请求充电量: {request.requested_amount} 度")
            print(f"创建时间: {request.created_at}")
            if request.charging_pile_id:
                pile = db.query(ChargingPile).filter(ChargingPile.id == request.charging_pile_id).first()
                print(f"已分配充电桩: {'快充桩' if pile.charging_mode == ChargingMode.FAST else '慢充桩'} {pile.pile_number}")
            else:
                print("尚未分配充电桩，仍在等候区")
                
            wait_time = estimate_wait_time(db, request.id)
            print(wait_time)
    finally:
        db.close()

if __name__ == "__main__":
    main() 