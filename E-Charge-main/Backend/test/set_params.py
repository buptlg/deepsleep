#!/usr/bin/env python3
"""
充电站系统参数配置工具
使用方法: python set_params.py
"""
import os
import argparse

def main():
    parser = argparse.ArgumentParser(description='设置充电站系统参数')
    parser.add_argument('--fast-piles', type=int, default=2, help='快充电桩数量 (默认: 2)')
    parser.add_argument('--trickle-piles', type=int, default=3, help='慢充电桩数量 (默认: 3)')
    parser.add_argument('--waiting-area', type=int, default=6, help='等候区车位容量 (默认: 6)')
    parser.add_argument('--queue-len', type=int, default=2, help='充电桩排队队列长度 (默认: 2)')
    
    args = parser.parse_args()
    
    # 生成.env文件
    env_file = os.path.join(os.path.dirname(__file__), '.env')
    with open(env_file, 'w') as f:
        f.write(f'FAST_CHARGING_PILE_NUM={args.fast_piles}\n')
        f.write(f'TRICKLE_CHARGING_PILE_NUM={args.trickle_piles}\n')
        f.write(f'WAITING_AREA_SIZE={args.waiting_area}\n')
        f.write(f'FAST_QUEUE_CAPACITY={args.waiting_area}\n')
        f.write(f'TRICKLE_QUEUE_CAPACITY={args.waiting_area}\n')
        f.write(f'CHARGING_QUEUE_LEN={args.queue_len}\n')
    
    print(f"参数已保存到 {env_file}")
    print("系统参数配置:")
    print(f"  快充电桩数量: {args.fast_piles}")
    print(f"  慢充电桩数量: {args.trickle_piles}")
    print(f"  等候区车位容量: {args.waiting_area}")
    print(f"  充电桩排队队列长度: {args.queue_len}")

if __name__ == "__main__":
    main() 