#!/usr/bin/env python3
print("测试开始")

from datetime import datetime, timedelta
from app.services.billing_service import BillingService

# 创建计费服务
billing_service = BillingService()
print("创建计费服务完成")

# 测试峰时+平时跨时段计费
start_time = datetime(2023, 11, 20, 14, 30)  # 14:30，峰时
end_time = datetime(2023, 11, 20, 16, 30)    # 16:30，平时
amount = 20.0  # 充电20度电

# 测试时间段划分
periods = billing_service.get_time_periods(start_time, end_time)
print(f"时间段划分结果:")
for start, end, rate in periods:
    rate_type = "峰时" if rate == 1.0 else ("平时" if rate == 0.7 else "谷时")
    print(f"  {start.strftime('%H:%M')} - {end.strftime('%H:%M')} => {rate_type}({rate}元/度)")

# 计算费用
electricity_fee, service_fee, total_fee = billing_service.calculate_fee(amount, start_time, end_time)

# 输出结果
print(f"\n充电时间: {start_time.strftime('%Y-%m-%d %H:%M')} 到 {end_time.strftime('%Y-%m-%d %H:%M')}")
print(f"充电量: {amount}度")
print(f"电费: {electricity_fee:.2f}元")
print(f"服务费: {service_fee:.2f}元")
print(f"总费用: {total_fee:.2f}元")

print("\n测试完成") 