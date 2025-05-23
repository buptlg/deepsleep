#!/usr/bin/env python3
from app.core.database import SessionLocal
from app.models.models import ChargingRequest, ChargingMode, ChargingPile, ChargingPileStatus
from sqlalchemy.orm import Session
from datetime import datetime

def check_charging_status(db: Session, fix_issues=False):
    """检查快充区和慢充区的充电状态"""
    print("==================== 充电状态检查 ====================")
    
    # 查询快充中的请求数量
    fast_charging = db.query(ChargingRequest).filter(
        ChargingRequest.charging_mode == ChargingMode.FAST,
        ChargingRequest.status == "charging"
    ).all()
    
    print(f"快充中车辆数: {len(fast_charging)}")
    for req in fast_charging:
        print(f"ID: {req.id}, 排队号: {req.queue_number}, 充电桩ID: {req.charging_pile_id}")
    
    # 查询快充区的充电桩数量和状态
    fast_piles = db.query(ChargingPile).filter(
        ChargingPile.charging_mode == ChargingMode.FAST
    ).all()
    
    print(f"\n快充电桩数量: {len(fast_piles)}")
    pile_request_counts = {}
    
    for pile in fast_piles:
        print(f"ID: {pile.id}, 编号: {pile.pile_number}, 状态: {pile.status.value}")
        
        # 查看该充电桩的充电请求
        pile_requests = db.query(ChargingRequest).filter(
            ChargingRequest.charging_pile_id == pile.id,
            ChargingRequest.status == "charging"
        ).all()
        
        pile_request_counts[pile.id] = len(pile_requests)
        print(f"  - 正在为 {len(pile_requests)} 辆车充电")
        for req in pile_requests:
            print(f"    排队号: {req.queue_number}, 请求ID: {req.id}")
    
    # 检查问题：每个快充桩最多只能为1辆车充电
    print("\n==================== 问题检查 ====================")
    has_issues = False
    
    for pile_id, count in pile_request_counts.items():
        if count > 1:
            has_issues = True
            pile = db.query(ChargingPile).filter(ChargingPile.id == pile_id).first()
            print(f"错误: 快充桩 {pile.pile_number} (ID: {pile_id}) 同时为 {count} 辆车充电，超过最大限制1辆")
    
    if not has_issues:
        print("未发现充电桩同时服务多辆车的问题")
    
    # 修复问题
    if fix_issues and has_issues:
        print("\n==================== 问题修复 ====================")
        fixed_count = 0
        
        for pile_id, count in pile_request_counts.items():
            if count > 1:
                pile = db.query(ChargingPile).filter(ChargingPile.id == pile_id).first()
                requests = db.query(ChargingRequest).filter(
                    ChargingRequest.charging_pile_id == pile_id,
                    ChargingRequest.status == "charging"
                ).order_by(ChargingRequest.created_at).all()
                
                # 保留最早的请求，其余改为等待状态
                keep_request = requests[0]
                print(f"保留最早的请求: ID: {keep_request.id}, 排队号: {keep_request.queue_number}")
                
                for req in requests[1:]:
                    req.status = "waiting"
                    fixed_count += 1
                    print(f"将请求改为等待状态: ID: {req.id}, 排队号: {req.queue_number}")
                
                db.commit()
                print(f"充电桩 {pile.pile_number} 的问题已修复")
        
        print(f"总共修复了 {fixed_count} 个问题")
        
        # 验证修复结果
        print("\n==================== 验证修复结果 ====================")
        for pile_id in pile_request_counts.keys():
            pile = db.query(ChargingPile).filter(ChargingPile.id == pile_id).first()
            charging_count = db.query(ChargingRequest).filter(
                ChargingRequest.charging_pile_id == pile_id,
                ChargingRequest.status == "charging"
            ).count()
            
            print(f"充电桩 {pile.pile_number} (ID: {pile_id}) 现在为 {charging_count} 辆车充电")

def check_charging_status_all():
    """检查所有充电桩的充电状态及相关车辆信息"""
    db = SessionLocal()
    try:
        print('== 充电桩状态及相关车辆信息 ==')
        
        # 查询所有充电桩
        piles = db.query(ChargingPile).all()
        print(f"系统共有 {len(piles)} 个充电桩")
        
        for pile in piles:
            print(f"\n充电桩 ID: {pile.id}, 编号: {pile.pile_number}, 类型: {pile.charging_mode.value}, 状态: {pile.status.value}")
            
            # 查询正在充电的车辆
            charging = db.query(ChargingRequest).filter(
                ChargingRequest.charging_pile_id == pile.id,
                ChargingRequest.status == 'charging'
            ).all()
            print(f"充电中车辆: {len(charging)}辆")
            for req in charging:
                started_time = req.started_at.strftime('%Y-%m-%d %H:%M:%S') if req.started_at else 'N/A'
                print(f"  - 排队号: {req.queue_number}, 用户ID: {req.user_id}, 请求充电量: {req.requested_amount}度, 开始充电时间: {started_time}")
            
            # 查询充电区等待的车辆
            waiting = db.query(ChargingRequest).filter(
                ChargingRequest.charging_pile_id == pile.id,
                ChargingRequest.status == 'waiting'
            ).order_by(ChargingRequest.created_at).all()
            print(f"充电区等待车辆: {len(waiting)}辆")
            for req in waiting:
                created_time = req.created_at.strftime('%Y-%m-%d %H:%M:%S')
                waiting_minutes = int((datetime.now() - req.created_at).total_seconds() / 60)
                print(f"  - 排队号: {req.queue_number}, 用户ID: {req.user_id}, 请求充电量: {req.requested_amount}度, 等待时间: {waiting_minutes}分钟")
        
        # 查询等候区等待的车辆（未分配充电桩）
        waiting_area = db.query(ChargingRequest).filter(
            ChargingRequest.charging_pile_id == None,
            ChargingRequest.status == 'waiting'
        ).order_by(ChargingRequest.created_at).all()
        print("\n等候区等待车辆(未分配充电桩):")
        print(f"共{len(waiting_area)}辆")
        for req in waiting_area:
            created_time = req.created_at.strftime('%Y-%m-%d %H:%M:%S')
            waiting_minutes = int((datetime.now() - req.created_at).total_seconds() / 60)
            print(f"  - 排队号: {req.queue_number}, 用户ID: {req.user_id}, 充电模式: {req.charging_mode.value}, " 
                  f"请求充电量: {req.requested_amount}度, 等待时间: {waiting_minutes}分钟")
            
        # 检查数据一致性问题
        print("\n== 数据一致性检查 ==")
        charging_status_issues = []
        
        # 检查是否有充电桩分配了多个正在充电的车辆
        for pile in piles:
            charging_count = db.query(ChargingRequest).filter(
                ChargingRequest.charging_pile_id == pile.id,
                ChargingRequest.status == 'charging'
            ).count()
            
            if charging_count > 1:
                charging_status_issues.append(f"错误: 充电桩 {pile.pile_number} (ID: {pile.id}) 有 {charging_count} 辆车同时充电")
        
        if charging_status_issues:
            print("\n发现数据一致性问题:")
            for issue in charging_status_issues:
                print(issue)
        else:
            print("未发现数据一致性问题")
            
    finally:
        db.close()

if __name__ == "__main__":
    db = SessionLocal()
    try:
        # 第二个参数设为True表示自动修复发现的问题
        check_charging_status(db, fix_issues=True)
    finally:
        db.close()

    check_charging_status_all() 