#!/usr/bin/env python3
"""
检查数据库中当前正在充电的车辆及其用户信息
"""
import sys
import os
from datetime import datetime
from sqlalchemy import create_engine, select, join
from sqlalchemy.orm import Session

# 添加项目根目录到系统路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入应用模型
from app.models.models import ChargingRequest, User, ChargingPile, Vehicle
from app.core.database import engine

def check_charging_vehicles():
    """查询并显示所有正在充电的车辆信息"""
    with Session(engine) as session:
        # 查询所有状态为charging的充电请求，并关联用户和充电桩信息
        query = (
            select(
                ChargingRequest.id, 
                ChargingRequest.queue_number,
                ChargingRequest.requested_amount,
                ChargingRequest.started_at,
                User.username, 
                Vehicle.battery_capacity,
                ChargingPile.pile_number, 
                ChargingPile.charging_mode,
                ChargingPile.power
            )
            .join(User, ChargingRequest.user_id == User.id)
            .join(ChargingPile, ChargingRequest.charging_pile_id == ChargingPile.id)
            .join(Vehicle, ChargingRequest.vehicle_id == Vehicle.id)
            .where(ChargingRequest.status == "charging")
            .order_by(ChargingRequest.started_at)
        )
        
        charging_vehicles = session.execute(query).all()
        
        if not charging_vehicles:
            print("当前没有车辆在充电")
            return
        
        print("\n当前正在充电的车辆:")
        print("=" * 80)
        print(f"{'ID':<5} {'排队号':<8} {'用户名':<15} {'充电桩':<8} {'充电模式':<8} {'请求电量':<8} {'已充电量':<8} {'进度':<8} {'已充电时间'}")
        print("-" * 80)
        
        for vehicle in charging_vehicles:
            # 计算已充电时间
            charging_time = datetime.now() - vehicle.started_at
            hours, remainder = divmod(charging_time.total_seconds(), 3600)
            minutes, seconds = divmod(remainder, 60)
            charging_time_str = f"{int(hours)}小时{int(minutes)}分钟"
            
            # 计算已充电量
            time_elapsed = charging_time.total_seconds() / 3600  # 小时
            # 确保已充电量不超过请求充电量
            calculated_amount = vehicle.power * time_elapsed
            charged_amount = round(min(calculated_amount, vehicle.requested_amount), 2)
            progress_percent = min(round((charged_amount / vehicle.requested_amount) * 100), 100)
            
            # 充电模式
            mode_str = "快充" if vehicle.charging_mode.value == "fast" else "慢充"
            
            print(f"{vehicle.id:<5} {vehicle.queue_number:<8} {vehicle.username:<15} {vehicle.pile_number:<8} "
                  f"{mode_str:<8} {vehicle.requested_amount:<8.2f} {charged_amount:<8.2f} "
                  f"{progress_percent:<6}% {charging_time_str}")
        
        print("=" * 80)
        print(f"共有 {len(charging_vehicles)} 辆车正在充电")

if __name__ == "__main__":
    check_charging_vehicles() 