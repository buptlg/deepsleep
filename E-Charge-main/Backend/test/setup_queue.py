#!/usr/bin/env python3
"""
充电桩排队队列配置工具
设置每个充电桩有2个车位（只有第一个车位可充电）的队列
"""
import os
import subprocess

def main():
    # 设置环境变量
    env_file = os.path.join(os.path.dirname(__file__), '.env')
    
    # 读取现有配置（如果存在）
    existing_config = {}
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    existing_config[key] = value
    
    # 更新配置
    existing_config['CHARGING_QUEUE_LEN'] = '2'
    
    # 固定充电站配置参数
    existing_config['FAST_CHARGING_PILE_NUM'] = '2'  # 2个快充电桩(A、B)
    existing_config['TRICKLE_CHARGING_PILE_NUM'] = '3'  # 3个慢充电桩(C、D、E)
    existing_config['WAITING_AREA_SIZE'] = '6'  # 等候区最大容量为6
    existing_config['FAST_QUEUE_CAPACITY'] = existing_config['WAITING_AREA_SIZE']
    existing_config['TRICKLE_QUEUE_CAPACITY'] = existing_config['WAITING_AREA_SIZE']
    
    # 写入配置文件
    with open(env_file, 'w') as f:
        for key, value in existing_config.items():
            f.write(f'{key}={value}\n')
    
    print("充电桩队列配置已更新")
    print("每个充电桩设置有等长的排队队列，长度为2个车位(只有第一个车位可充电)")
    print(f"配置已保存到 {env_file}")

if __name__ == "__main__":
    main() 