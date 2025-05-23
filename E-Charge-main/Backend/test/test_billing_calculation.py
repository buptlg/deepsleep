#!/usr/bin/env python3
print("开始测试费用计算功能")

from datetime import datetime, timedelta
from app.services.billing_service import BillingService

# 创建服务实例
billing = BillingService()

# 测试场景1：跨峰时和平时的充电
start_time = datetime(2023, 11, 20, 14, 30)  # 14:30，峰时
end_time = datetime(2023, 11, 20, 16, 30)    # 16:30，平时
amount = 20.0  # 充电20度电

# 计算费用
electricity_fee, service_fee, total_fee = billing.calculate_fee(amount, start_time, end_time)

# 手动计算预期费用
total_duration = 2.0  # 总时长2小时
peak_duration = 0.5  # 峰时0.5小时 (14:30-15:00)
normal_duration = 1.5  # 平时1.5小时 (15:00-16:30)

peak_ratio = peak_duration / total_duration
normal_ratio = normal_duration / total_duration

peak_amount = amount * peak_ratio
normal_amount = amount * normal_ratio

expected_electricity_fee = peak_amount * 1.0 + normal_amount * 0.7
expected_service_fee = amount * 0.8
expected_total_fee = expected_electricity_fee + expected_service_fee

print(f"\n测试场景1：从 {start_time.strftime('%Y-%m-%d %H:%M')} 到 {end_time.strftime('%Y-%m-%d %H:%M')}")
print(f"充电量: {amount}度")
print(f"峰时段: {peak_duration}小时 ({peak_ratio:.2%}), 平时段: {normal_duration}小时 ({normal_ratio:.2%})")
print(f"电费: {electricity_fee:.2f}元 (期望: {expected_electricity_fee:.2f}元)")
print(f"服务费: {service_fee:.2f}元 (期望: {expected_service_fee:.2f}元)")
print(f"总费用: {total_fee:.2f}元 (期望: {expected_total_fee:.2f}元)")
print(f"计算结果{'正确' if abs(total_fee - expected_total_fee) < 0.01 else '错误'}")

# 测试场景2：跨多个时段的充电
start_time = datetime(2023, 11, 20, 9, 0)   # 9:00，平时
end_time = datetime(2023, 11, 20, 19, 0)    # 19:00，峰时
amount = 40.0  # 充电40度电

# 计算费用
electricity_fee, service_fee, total_fee = billing.calculate_fee(amount, start_time, end_time)

# 手动计算预期费用
total_duration = 10.0  # 总时长10小时
normal_duration1 = 1.0  # 平时1小时 (9:00-10:00)
peak_duration1 = 5.0    # 峰时5小时 (10:00-15:00)
normal_duration2 = 3.0  # 平时3小时 (15:00-18:00)
peak_duration2 = 1.0    # 峰时1小时 (18:00-19:00)

normal_ratio = (normal_duration1 + normal_duration2) / total_duration
peak_ratio = (peak_duration1 + peak_duration2) / total_duration

normal_amount = amount * normal_ratio
peak_amount = amount * peak_ratio

expected_electricity_fee = normal_amount * 0.7 + peak_amount * 1.0
expected_service_fee = amount * 0.8
expected_total_fee = expected_electricity_fee + expected_service_fee

print(f"\n测试场景2：从 {start_time.strftime('%Y-%m-%d %H:%M')} 到 {end_time.strftime('%Y-%m-%d %H:%M')}")
print(f"充电量: {amount}度")
print(f"平时段: {normal_duration1 + normal_duration2}小时 ({normal_ratio:.2%}), 峰时段: {peak_duration1 + peak_duration2}小时 ({peak_ratio:.2%})")
print(f"电费: {electricity_fee:.2f}元 (期望: {expected_electricity_fee:.2f}元)")
print(f"服务费: {service_fee:.2f}元 (期望: {expected_service_fee:.2f}元)")
print(f"总费用: {total_fee:.2f}元 (期望: {expected_total_fee:.2f}元)")
print(f"计算结果{'正确' if abs(total_fee - expected_total_fee) < 0.01 else '错误'}")

# 测试场景3：跨天的充电
start_time = datetime(2023, 11, 20, 22, 0)  # 22:00，平时
end_time = datetime(2023, 11, 21, 8, 0)     # 次日8:00，平时
amount = 30.0  # 充电30度电

# 计算费用
electricity_fee, service_fee, total_fee = billing.calculate_fee(amount, start_time, end_time)

# 手动计算预期费用
total_duration = 10.0  # 总时长10小时
normal_duration1 = 1.0  # 平时1小时 (22:00-23:00)
valley_duration = 8.0   # 谷时8小时 (23:00-次日7:00)
normal_duration2 = 1.0  # 平时1小时 (7:00-8:00)

normal_ratio = (normal_duration1 + normal_duration2) / total_duration
valley_ratio = valley_duration / total_duration

normal_amount = amount * normal_ratio
valley_amount = amount * valley_ratio

expected_electricity_fee = normal_amount * 0.7 + valley_amount * 0.4
expected_service_fee = amount * 0.8
expected_total_fee = expected_electricity_fee + expected_service_fee

print(f"\n测试场景3：从 {start_time.strftime('%Y-%m-%d %H:%M')} 到 {end_time.strftime('%Y-%m-%d %H:%M')}")
print(f"充电量: {amount}度")
print(f"平时段: {normal_duration1 + normal_duration2}小时 ({normal_ratio:.2%}), 谷时段: {valley_duration}小时 ({valley_ratio:.2%})")
print(f"电费: {electricity_fee:.2f}元 (期望: {expected_electricity_fee:.2f}元)")
print(f"服务费: {service_fee:.2f}元 (期望: {expected_service_fee:.2f}元)")
print(f"总费用: {total_fee:.2f}元 (期望: {expected_total_fee:.2f}元)")
print(f"计算结果{'正确' if abs(total_fee - expected_total_fee) < 0.01 else '错误'}")

print("\n测试完成") 