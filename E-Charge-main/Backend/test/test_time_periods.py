#!/usr/bin/env python3
print("开始测试时间段划分功能")

from datetime import datetime, timedelta
from app.services.billing_service import BillingService

# 创建服务实例
billing = BillingService()

# 测试场景1：跨峰时和平时的充电
start_time = datetime(2023, 11, 20, 14, 30)  # 14:30，峰时
end_time = datetime(2023, 11, 20, 16, 30)    # 16:30，平时

print(f"\n测试场景1：从 {start_time.strftime('%Y-%m-%d %H:%M')} 到 {end_time.strftime('%Y-%m-%d %H:%M')}")
periods = billing.get_time_periods(start_time, end_time)
print(f"划分结果：")
for i, (start, end, rate) in enumerate(periods):
    rate_type = "峰时" if rate == 1.0 else ("平时" if rate == 0.7 else "谷时")
    print(f"  段{i+1}: {start.strftime('%H:%M')} - {end.strftime('%H:%M')} => {rate_type}({rate}元/度)")

# 测试场景2：跨多个时段的充电
start_time = datetime(2023, 11, 20, 9, 0)   # 9:00，平时
end_time = datetime(2023, 11, 20, 19, 0)    # 19:00，峰时

print(f"\n测试场景2：从 {start_time.strftime('%Y-%m-%d %H:%M')} 到 {end_time.strftime('%Y-%m-%d %H:%M')}")
periods = billing.get_time_periods(start_time, end_time)
print(f"划分结果：")
for i, (start, end, rate) in enumerate(periods):
    rate_type = "峰时" if rate == 1.0 else ("平时" if rate == 0.7 else "谷时")
    print(f"  段{i+1}: {start.strftime('%H:%M')} - {end.strftime('%H:%M')} => {rate_type}({rate}元/度)")

# 测试场景3：跨天的充电
start_time = datetime(2023, 11, 20, 22, 0)  # 22:00，平时
end_time = datetime(2023, 11, 21, 8, 0)     # 次日8:00，平时

print(f"\n测试场景3：从 {start_time.strftime('%Y-%m-%d %H:%M')} 到 {end_time.strftime('%Y-%m-%d %H:%M')}")
periods = billing.get_time_periods(start_time, end_time)
print(f"划分结果：")
for i, (start, end, rate) in enumerate(periods):
    rate_type = "峰时" if rate == 1.0 else ("平时" if rate == 0.7 else "谷时")
    duration = (end - start).total_seconds() / 3600
    print(f"  段{i+1}: {start.strftime('%Y-%m-%d %H:%M')} - {end.strftime('%Y-%m-%d %H:%M')} ({duration:.1f}小时) => {rate_type}({rate}元/度)")

print("\n测试完成") 