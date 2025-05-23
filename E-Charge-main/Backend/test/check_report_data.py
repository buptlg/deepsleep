#!/usr/bin/env python3
"""
检查数据库中的报表数据
"""
import sys
import os
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

# 添加项目根目录到系统路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入应用模型
from app.models.models import ChargingDetail, ChargingPile, ChargingRequest, User
from app.core.database import engine

def check_report_data():
    """检查报表相关数据"""
    with Session(engine) as session:
        print("=== 数据库报表数据检查 ===\n")
        
        # 检查充电详单数据
        total_details = session.query(ChargingDetail).count()
        print(f"充电详单总数: {total_details}")
        
        if total_details > 0:
            # 显示最近的几条记录
            recent_details = session.query(ChargingDetail).order_by(
                ChargingDetail.start_time.desc()
            ).limit(5).all()
            
            print("\n最近的充电详单:")
            print("ID  | 充电桩ID | 开始时间             | 结束时间             | 充电量  | 总费用")
            print("-" * 80)
            for detail in recent_details:
                print(f"{detail.id:<3} | {detail.charging_pile_id:<7} | {detail.start_time} | {detail.end_time} | {detail.charging_amount:<6.2f} | {detail.total_fee:<6.2f}")
            
            # 按充电桩统计
            print("\n按充电桩统计:")
            pile_stats = {}
            all_details = session.query(ChargingDetail).all()
            for detail in all_details:
                pile_id = detail.charging_pile_id
                if pile_id not in pile_stats:
                    pile_stats[pile_id] = {
                        'count': 0,
                        'total_amount': 0,
                        'total_fee': 0
                    }
                pile_stats[pile_id]['count'] += 1
                pile_stats[pile_id]['total_amount'] += detail.charging_amount
                pile_stats[pile_id]['total_fee'] += detail.total_fee
            
            print("充电桩ID | 充电次数 | 总充电量 | 总费用")
            print("-" * 40)
            for pile_id, stats in pile_stats.items():
                print(f"{pile_id:<7} | {stats['count']:<7} | {stats['total_amount']:<7.2f} | {stats['total_fee']:<7.2f}")
        
        # 检查充电桩数据
        total_piles = session.query(ChargingPile).count()
        print(f"\n充电桩总数: {total_piles}")
        
        if total_piles > 0:
            piles = session.query(ChargingPile).all()
            print("充电桩列表:")
            print("ID | 编号 | 类型 | 功率 | 状态")
            print("-" * 35)
            for pile in piles:
                print(f"{pile.id:<2} | {pile.pile_number:<4} | {pile.charging_mode.value:<4} | {pile.power:<4} | {pile.status.value}")
        
        # 检查充电请求数据
        total_requests = session.query(ChargingRequest).count()
        completed_requests = session.query(ChargingRequest).filter(
            ChargingRequest.status == "completed"
        ).count()
        
        print(f"\n充电请求总数: {total_requests}")
        print(f"已完成的充电请求: {completed_requests}")
        
        # 检查今日数据
        today = datetime.now().date()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())
        
        today_details = session.query(ChargingDetail).filter(
            ChargingDetail.start_time >= today_start,
            ChargingDetail.end_time <= today_end
        ).count()
        
        print(f"今日充电详单: {today_details}")
        
        # 检查本周数据
        week_start = today_start - timedelta(days=today.weekday())
        week_details = session.query(ChargingDetail).filter(
            ChargingDetail.start_time >= week_start,
            ChargingDetail.end_time <= today_end
        ).count()
        
        print(f"本周充电详单: {week_details}")
        
        # 检查本月数据
        month_start = datetime(today.year, today.month, 1)
        month_details = session.query(ChargingDetail).filter(
            ChargingDetail.start_time >= month_start,
            ChargingDetail.end_time <= today_end
        ).count()
        
        print(f"本月充电详单: {month_details}")
        
        print("\n=== 检查完成 ===")
        
        if total_details == 0:
            print("\n⚠️  警告: 数据库中没有充电详单数据！")
            print("   这可能导致报表显示为空。")
            print("   建议: 进行一些完整的充电流程来生成测试数据。")

if __name__ == "__main__":
    check_report_data() 