"""
查询数据库中充电和排队状态
运行方法: python scripts/query_charging_status.py
"""

import sys
import os

# 添加项目根目录到 Python 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
root_dir = os.path.dirname(parent_dir)
sys.path.append(root_dir)

from Backend.app.core.database import SessionLocal
from Backend.app.models.models import ChargingRequest, User, ChargingPile, ChargingMode
from sqlalchemy.orm import joinedload
from sqlalchemy import text

def query_charging_status():
    """查询数据库中充电和排队状态"""
    db = SessionLocal()
    try:
        print("========== 充电站状态查询 ==========")
        
        # 打印所有表
        result = db.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
        tables = [row[0] for row in result]
        print(f"数据库中的表: {tables}")
        
        # 打印充电请求表的所有记录
        result = db.execute(text("SELECT id, user_id, queue_number, charging_mode, status, charging_pile_id FROM charging_requests;"))
        print("\n所有充电请求记录:")
        for row in result:
            print(f"ID: {row[0]}, 用户ID: {row[1]}, 排队号: {row[2]}, 充电模式: {row[3]}, 状态: {row[4]}, 充电桩ID: {row[5]}")
        
        # 1. 查询充电区正在充电的用户
        charging_users = db.query(ChargingRequest).filter(
            ChargingRequest.status == "charging",
            ChargingRequest.charging_pile_id.isnot(None)
        ).options(joinedload(ChargingRequest.user), joinedload(ChargingRequest.charging_pile)).all()
        
        print("\n--- 充电区正在充电的用户 ---")
        if charging_users:
            for req in charging_users:
                pile_type = "快充桩" if req.charging_pile.charging_mode == ChargingMode.FAST else "慢充桩"
                print(f"用户名: {req.user.username}, 排队号: {req.queue_number}, 充电桩: {pile_type} {req.charging_pile.pile_number}")
        else:
            print("当前无用户正在充电")
        
        # 2. 查询充电区等待的用户（已分配充电桩但仍在等待的用户）
        charging_area_waiting_users = db.query(ChargingRequest).filter(
            ChargingRequest.status == "waiting",
            ChargingRequest.charging_pile_id.isnot(None)
        ).options(joinedload(ChargingRequest.user), joinedload(ChargingRequest.charging_pile)).all()
        
        print("\n--- 充电区等待的用户 ---")
        if charging_area_waiting_users:
            for req in charging_area_waiting_users:
                pile_type = "快充桩" if req.charging_pile.charging_mode == ChargingMode.FAST else "慢充桩"
                print(f"用户名: {req.user.username}, 排队号: {req.queue_number}, 分配充电桩: {pile_type} {req.charging_pile.pile_number}")
        else:
            print("当前充电区无等待用户")
        
        # 3. 查询等待区等待的用户（未分配充电桩的等待用户）
        waiting_area_users = db.query(ChargingRequest).filter(
            ChargingRequest.status == "waiting",
            ChargingRequest.charging_pile_id.is_(None)
        ).options(joinedload(ChargingRequest.user)).all()
        
        print("\n--- 等待区等待的用户 ---")
        print(f"找到{len(waiting_area_users)}个等待区用户")
        if waiting_area_users:
            # 分组显示快充和慢充
            fast_waiting = [req for req in waiting_area_users if req.charging_mode == ChargingMode.FAST]
            trickle_waiting = [req for req in waiting_area_users if req.charging_mode == ChargingMode.TRICKLE]
            
            print(f"快充等待用户: {len(fast_waiting)}, 慢充等待用户: {len(trickle_waiting)}")
            
            if fast_waiting:
                print("快充等待区:")
                for req in fast_waiting:
                    print(f"用户名: {req.user.username}, 排队号: {req.queue_number}, 请求充电量: {req.requested_amount}度")
            else:
                print("快充等待区: 无等待用户")
            
            if trickle_waiting:
                print("慢充等待区:")
                for req in trickle_waiting:
                    print(f"用户名: {req.user.username}, 排队号: {req.queue_number}, 请求充电量: {req.requested_amount}度")
            else:
                print("慢充等待区: 无等待用户")
        else:
            print("当前等待区无等待用户")
        
        # 4. 统计信息
        total_charging = len(charging_users)
        total_waiting_in_charging_area = len(charging_area_waiting_users)
        total_waiting_in_waiting_area = len(waiting_area_users)
        
        print("\n--- 统计信息 ---")
        print(f"充电中用户数: {total_charging}")
        print(f"充电区等待用户数: {total_waiting_in_charging_area}")
        print(f"等待区等待用户数: {total_waiting_in_waiting_area}")
        print(f"总排队用户数: {total_waiting_in_charging_area + total_waiting_in_waiting_area}")
        
    except Exception as e:
        print(f"查询数据时发生错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    query_charging_status() 