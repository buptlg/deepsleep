#!/usr/bin/env python3
"""
充电站配置设置工具
根据需求设置充电站的完整配置
"""
import os
import subprocess
import sys

def setup_charging_station():
    """设置符合需求的充电站配置"""
    # 设置环境变量
    env_file = os.path.join(os.path.dirname(__file__), '.env')
    
    # 配置参数
    config = {
        # 快充电桩数量：2个(A、B)
        'FAST_CHARGING_PILE_NUM': '2',
        
        # 慢充电桩数量：3个(C、D、E)
        'TRICKLE_CHARGING_PILE_NUM': '3',
        
        # 等候区最大车位容量：6个
        'WAITING_AREA_SIZE': '6',
        
        # 等候区容量配置（与WAITING_AREA_SIZE保持一致）
        'FAST_QUEUE_CAPACITY': '6',
        'TRICKLE_QUEUE_CAPACITY': '6',
        
        # 充电桩排队队列长度：2个车位
        'CHARGING_QUEUE_LEN': '2'
    }
    
    # 写入配置文件
    with open(env_file, 'w') as f:
        for key, value in config.items():
            f.write(f'{key}={value}\n')
    
    print("=============== 充电站配置完成 ===============")
    print("充电站系统配置如下：")
    print("1. 等候区：")
    print(f"   - 最大车位容量: {config['WAITING_AREA_SIZE']}个")
    print("   - 排队方式: 快充F类型号码(F1、F2...)，慢充T类型号码(T1、T2...)")
    print("2. 充电区：")
    print(f"   - 快充电桩: {config['FAST_CHARGING_PILE_NUM']}个(A、B)，功率30度/小时")
    print(f"   - 慢充电桩: {config['TRICKLE_CHARGING_PILE_NUM']}个(C、D、E)，功率7度/小时")
    print(f"   - 排队队列: 每个充电桩{config['CHARGING_QUEUE_LEN']}个车位，只有第一个车位可充电")
    print("3. 调度策略:")
    print("   - 先来先到叫号")
    print("   - 选择完成充电所需时长最短的充电桩")
    print(f"配置已保存到 {env_file}")
    
    # 提示重启服务器
    print("\n提示: 请重启服务器使配置生效")
    print("uvicorn app.main:app --reload")

if __name__ == "__main__":
    setup_charging_station() 