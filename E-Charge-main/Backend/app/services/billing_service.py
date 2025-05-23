from datetime import datetime, time, timedelta
from typing import Tuple, List

class BillingService:
    def __init__(self):
        self.service_fee_rate = 0.8  # 服务费单价（元/度）
        self.peak_rate = 1.0  # 峰时电价（元/度）
        self.normal_rate = 0.7  # 平时电价（元/度）
        self.valley_rate = 0.4  # 谷时电价（元/度）

    def get_electricity_rate(self, current_time: datetime) -> float:
        """根据时间获取电价"""
        current_hour = current_time.time().hour
        
        # 峰时：10:00-15:00, 18:00-21:00
        if (10 <= current_hour < 15) or (18 <= current_hour < 21):
            return self.peak_rate
        # 平时：7:00-10:00, 15:00-18:00, 21:00-23:00
        elif (7 <= current_hour < 10) or (15 <= current_hour < 18) or (21 <= current_hour < 23):
            return self.normal_rate
        # 谷时：23:00-次日7:00
        else:
            return self.valley_rate

    def get_time_periods(self, start_time: datetime, end_time: datetime) -> List[Tuple[datetime, datetime, float]]:
        """
        将充电时间分割为不同费率的时间段
        
        Args:
            start_time: 充电开始时间
            end_time: 充电结束时间
            
        Returns:
            List[Tuple[datetime, datetime, float]]: 时间段列表，每个元素为(开始时间, 结束时间, 电价)
        """
        if start_time >= end_time:
            return []
            
        periods = []
        current = start_time
        
        while current < end_time:
            # 计算当前费率
            rate = self.get_electricity_rate(current)
            
            # 计算当前费率时段的结束时间
            hour = current.hour
            
            if 7 <= hour < 10:
                # 平时 7:00-10:00
                next_rate_change = datetime(current.year, current.month, current.day, 10, 0)
            elif 10 <= hour < 15:
                # 峰时 10:00-15:00
                next_rate_change = datetime(current.year, current.month, current.day, 15, 0)
            elif 15 <= hour < 18:
                # 平时 15:00-18:00
                next_rate_change = datetime(current.year, current.month, current.day, 18, 0)
            elif 18 <= hour < 21:
                # 峰时 18:00-21:00
                next_rate_change = datetime(current.year, current.month, current.day, 21, 0)
            elif 21 <= hour < 23:
                # 平时 21:00-23:00
                next_rate_change = datetime(current.year, current.month, current.day, 23, 0)
            else:
                # 谷时 23:00-次日7:00
                if hour >= 23:
                    next_day = current + timedelta(days=1)
                    next_rate_change = datetime(next_day.year, next_day.month, next_day.day, 7, 0)
                else:
                    next_rate_change = datetime(current.year, current.month, current.day, 7, 0)
            
            # 确保不超过充电结束时间
            period_end = min(next_rate_change, end_time)
            
            # 添加时段
            periods.append((current, period_end, rate))
            
            # 移动到下一个时段
            current = period_end
        
        return periods

    def calculate_fee(self, charging_amount: float, start_time: datetime, end_time: datetime) -> Tuple[float, float, float]:
        """计算充电费用
        
        Args:
            charging_amount: 充电量（度）
            start_time: 开始充电时间
            end_time: 结束充电时间
            
        Returns:
            Tuple[float, float, float]: (充电费用, 服务费用, 总费用)
        """
        # 计算服务费
        service_fee = charging_amount * self.service_fee_rate

        # 获取不同电价时段
        periods = self.get_time_periods(start_time, end_time)
        
        if not periods:
            # 如果没有有效的时间段，使用开始时间的电价计算（兼容旧逻辑）
            electricity_rate = self.get_electricity_rate(start_time)
            electricity_fee = charging_amount * electricity_rate
        else:
            # 计算充电总时长（小时）
            total_duration = (end_time - start_time).total_seconds() / 3600
            
            # 计算每个时段的电费
            electricity_fee = 0.0
            for period_start, period_end, rate in periods:
                # 计算当前时段的时长占总时长的比例
                period_duration = (period_end - period_start).total_seconds() / 3600
                period_ratio = period_duration / total_duration
                
                # 计算当前时段消耗的电量
                period_amount = charging_amount * period_ratio
                
                # 计算当前时段的电费
                electricity_fee += period_amount * rate

        # 计算总费用
        total_fee = electricity_fee + service_fee

        return electricity_fee, service_fee, total_fee 