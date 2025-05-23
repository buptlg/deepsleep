"""
清除数据库中的排队和充电信息
运行方法: python scripts/clear_charging_data.py
"""

import sys
import os

# 添加项目根目录到 Python 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
root_dir = os.path.dirname(parent_dir)
sys.path.append(root_dir)

from Backend.app.core.database import SessionLocal, engine
from Backend.app.models.models import ChargingRequest, ChargingDetail, ChargingPile, ChargingPileStatus
from sqlalchemy import text

def clear_charging_data():
    """清除所有充电请求和详单数据，并重置充电桩状态"""
    db = SessionLocal()
    try:
        # 获取数据库中所有表名
        result = db.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
        tables = [row[0] for row in result]
        print(f"数据库中的表: {tables}")
        
        print("正在清除充电详单...")
        if "charging_details" in tables:
            db.execute(text("DELETE FROM charging_details"))
            print("充电详单已清除")
        else:
            print("表 'charging_details' 不存在，跳过")
        
        print("正在清除充电请求...")
        if "charging_requests" in tables:
            db.execute(text("DELETE FROM charging_requests"))
            print("充电请求已清除")
        else:
            print("表 'charging_requests' 不存在，跳过")
        
        print("正在重置充电桩状态...")
        # 将所有充电桩状态重置为可用
        if "charging_piles" in tables:
            charging_piles = db.query(ChargingPile).all()
            for pile in charging_piles:
                pile.status = ChargingPileStatus.AVAILABLE
            print(f"已重置 {len(charging_piles)} 个充电桩状态")
        else:
            print("表 'charging_piles' 不存在，跳过")
        
        # 提交事务
        db.commit()
        print("数据清除完成！")
    except Exception as e:
        db.rollback()
        print(f"清除数据时发生错误: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    # 确认操作
    confirm = input("警告: 此操作将清除所有充电请求和详单数据，并重置充电桩状态。确定要继续吗？(y/n): ")
    if confirm.lower() == 'y':
        clear_charging_data()
    else:
        print("操作已取消") 