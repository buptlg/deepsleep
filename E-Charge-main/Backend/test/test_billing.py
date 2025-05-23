#!/usr/bin/env python3
from datetime import datetime, timedelta
from app.services.billing_service import BillingService

print("开始测试计费服务...")

def test_billing_service():
    """测试计费服务是否正确计算不同时间段的电费"""
    billing_service = BillingService()
    
    print("已创建BillingService实例")
    
    # 测试单一时段内的计费（峰时）
    peak_start = datetime(2023, 11, 20, 11, 0)  # 11:00，峰时
    peak_end = datetime(2023, 11, 20, 12, 0)    # 12:00，峰时
    amount = 10.0  # 充电10度电
    
    electricity_fee, service_fee, total_fee = billing_service.calculate_fee(amount, peak_start, peak_end)
    expected_electricity_fee = amount * 1.0  # 峰时电价1.0元/度
    expected_service_fee = amount * 0.8     # 服务费0.8元/度
    expected_total_fee = expected_electricity_fee + expected_service_fee
    
    print("\n测试1: 纯峰时段充电")
    print(f"充电时间: {peak_start.strftime('%Y-%m-%d %H:%M')} 到 {peak_end.strftime('%Y-%m-%d %H:%M')}")
    print(f"充电量: {amount}度")
    print(f"电费: {electricity_fee:.2f}元 (期望: {expected_electricity_fee:.2f}元)")
    print(f"服务费: {service_fee:.2f}元 (期望: {expected_service_fee:.2f}元)")
    print(f"总费用: {total_fee:.2f}元 (期望: {expected_total_fee:.2f}元)")
    print(f"计算结果{'正确' if abs(total_fee - expected_total_fee) < 0.01 else '错误'}")
    
    # 测试跨时段计费（峰时+平时）
    mixed_start = datetime(2023, 11, 20, 14, 30)  # 14:30，峰时
    mixed_end = datetime(2023, 11, 20, 16, 30)    # 16:30，平时
    amount = 20.0  # 充电20度电
    
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
    
    electricity_fee, service_fee, total_fee = billing_service.calculate_fee(amount, mixed_start, mixed_end)
    
    print("\n测试2: 峰时+平时跨时段充电")
    print(f"充电时间: {mixed_start.strftime('%Y-%m-%d %H:%M')} 到 {mixed_end.strftime('%Y-%m-%d %H:%M')}")
    print(f"充电量: {amount}度")
    print(f"峰时段: {peak_duration}小时 ({peak_ratio:.2%}), 平时段: {normal_duration}小时 ({normal_ratio:.2%})")
    print(f"电费: {electricity_fee:.2f}元 (期望: {expected_electricity_fee:.2f}元)")
    print(f"服务费: {service_fee:.2f}元 (期望: {expected_service_fee:.2f}元)")
    print(f"总费用: {total_fee:.2f}元 (期望: {expected_total_fee:.2f}元)")
    print(f"计算结果{'正确' if abs(total_fee - expected_total_fee) < 0.01 else '错误'}")
    
    # 测试跨多时段计费（平时+峰时+平时）
    complex_start = datetime(2023, 11, 20, 9, 0)   # 9:00，平时
    complex_end = datetime(2023, 11, 20, 19, 0)    # 19:00，峰时
    amount = 40.0  # 充电40度电
    
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
    
    electricity_fee, service_fee, total_fee = billing_service.calculate_fee(amount, complex_start, complex_end)
    
    print("\n测试3: 复杂多时段充电")
    print(f"充电时间: {complex_start.strftime('%Y-%m-%d %H:%M')} 到 {complex_end.strftime('%Y-%m-%d %H:%M')}")
    print(f"充电量: {amount}度")
    print(f"平时段: {normal_duration1 + normal_duration2}小时 ({normal_ratio:.2%}), 峰时段: {peak_duration1 + peak_duration2}小时 ({peak_ratio:.2%})")
    print(f"电费: {electricity_fee:.2f}元 (期望: {expected_electricity_fee:.2f}元)")
    print(f"服务费: {service_fee:.2f}元 (期望: {expected_service_fee:.2f}元)")
    print(f"总费用: {total_fee:.2f}元 (期望: {expected_total_fee:.2f}元)")
    print(f"计算结果{'正确' if abs(total_fee - expected_total_fee) < 0.01 else '错误'}")
    
    # 测试谷时计费
    valley_start = datetime(2023, 11, 20, 1, 0)    # 1:00，谷时
    valley_end = datetime(2023, 11, 20, 6, 0)      # 6:00，谷时
    amount = 15.0  # 充电15度电
    
    electricity_fee, service_fee, total_fee = billing_service.calculate_fee(amount, valley_start, valley_end)
    expected_electricity_fee = amount * 0.4  # 谷时电价0.4元/度
    expected_service_fee = amount * 0.8      # 服务费0.8元/度
    expected_total_fee = expected_electricity_fee + expected_service_fee
    
    print("\n测试4: 谷时段充电")
    print(f"充电时间: {valley_start.strftime('%Y-%m-%d %H:%M')} 到 {valley_end.strftime('%Y-%m-%d %H:%M')}")
    print(f"充电量: {amount}度")
    print(f"电费: {electricity_fee:.2f}元 (期望: {expected_electricity_fee:.2f}元)")
    print(f"服务费: {service_fee:.2f}元 (期望: {expected_service_fee:.2f}元)")
    print(f"总费用: {total_fee:.2f}元 (期望: {expected_total_fee:.2f}元)")
    print(f"计算结果{'正确' if abs(total_fee - expected_total_fee) < 0.01 else '错误'}")
    
    # 测试跨天计费（谷时跨天）
    cross_day_start = datetime(2023, 11, 20, 22, 0)  # 22:00，平时
    cross_day_end = datetime(2023, 11, 21, 8, 0)     # 次日8:00，平时
    amount = 30.0  # 充电30度电
    
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
    
    electricity_fee, service_fee, total_fee = billing_service.calculate_fee(amount, cross_day_start, cross_day_end)
    
    print("\n测试5: 跨天谷时充电")
    print(f"充电时间: {cross_day_start.strftime('%Y-%m-%d %H:%M')} 到 {cross_day_end.strftime('%Y-%m-%d %H:%M')}")
    print(f"充电量: {amount}度")
    print(f"平时段: {normal_duration1 + normal_duration2}小时 ({normal_ratio:.2%}), 谷时段: {valley_duration}小时 ({valley_ratio:.2%})")
    print(f"电费: {electricity_fee:.2f}元 (期望: {expected_electricity_fee:.2f}元)")
    print(f"服务费: {service_fee:.2f}元 (期望: {expected_service_fee:.2f}元)")
    print(f"总费用: {total_fee:.2f}元 (期望: {expected_total_fee:.2f}元)")
    print(f"计算结果{'正确' if abs(total_fee - expected_total_fee) < 0.01 else '错误'}")
    
    # 打印时间段划分结果
    print("\n时间段划分测试:")
    periods = billing_service.get_time_periods(complex_start, complex_end)
    print(f"从 {complex_start.strftime('%Y-%m-%d %H:%M')} 到 {complex_end.strftime('%Y-%m-%d %H:%M')} 的时间段划分:")
    for i, (start, end, rate) in enumerate(periods):
        rate_type = "峰时" if rate == 1.0 else ("平时" if rate == 0.7 else "谷时")
        print(f"  段{i+1}: {start.strftime('%H:%M')} - {end.strftime('%H:%M')} => {rate_type}({rate}元/度)")

if __name__ == "__main__":
    test_billing_service()
else:
    print("直接调用测试函数")
    test_billing_service() 