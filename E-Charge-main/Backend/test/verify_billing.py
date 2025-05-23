#!/usr/bin/env python3
print("开始验证计费服务属性")

# 导入计费服务
from app.services.billing_service import BillingService

# 创建服务实例
billing = BillingService()

# 打印属性
print(f'服务费率: {billing.service_fee_rate}元/度')
print(f'峰时电价: {billing.peak_rate}元/度')
print(f'平时电价: {billing.normal_rate}元/度')
print(f'谷时电价: {billing.valley_rate}元/度')

print("验证完成") 