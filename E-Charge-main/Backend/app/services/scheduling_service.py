from datetime import datetime
from typing import List, Dict
from sqlalchemy.orm import Session
from ..models.models import ChargingRequest, ChargingPile, ChargingMode, ChargingPileStatus
from ..core.config import settings

class SchedulingService:
    def __init__(self, db: Session):
        self.db = db
        self.fast_pile_power = 30  # 快充功率（度/小时）
        self.trickle_pile_power = 7  # 慢充功率（度/小时）
        # 充电桩排队队列长度
        self.charging_queue_len = settings.CHARGING_QUEUE_LEN

    def calculate_charging_time(self, amount: float, power: float) -> float:
        """计算充电所需时间（小时）"""
        return amount / power

    def get_available_piles(self, charging_mode: ChargingMode) -> List[ChargingPile]:
        """获取可用的充电桩"""
        # 获取该充电模式下的所有充电桩
        piles = self.db.query(ChargingPile).filter(
            ChargingPile.charging_mode == charging_mode,
            ChargingPile.status.in_([ChargingPileStatus.AVAILABLE, ChargingPileStatus.OCCUPIED])
        ).all()
        
        # 筛选出队列未满的充电桩
        available_piles = []
        for pile in piles:
            # 查询该充电桩当前排队的车辆数量（包括充电中和等待中的）
            queue_count = self.db.query(ChargingRequest).filter(
                ChargingRequest.charging_pile_id == pile.id,
                ChargingRequest.status.in_(["charging", "waiting"])
            ).count()
            
            # 如果排队数量小于队列长度上限，则视为可用
            if queue_count < self.charging_queue_len:
                available_piles.append(pile)
        
        return available_piles

    def calculate_total_charging_time(self, request: ChargingRequest, pile: ChargingPile) -> float:
        """计算总充电时间（等待时间 + 充电时间）"""
        # 获取当前充电桩队列中的请求，按创建时间排序，保证先来先充电
        queue_requests = self.db.query(ChargingRequest).filter(
            ChargingRequest.charging_pile_id == pile.id,
            ChargingRequest.status.in_(["charging", "waiting"])
        ).order_by(ChargingRequest.created_at).all()

        # 计算等待时间
        # 只有第一个车位可充电，所以等待时间是前面所有车辆的充电时间总和
        wait_time = 0
        for req in queue_requests:
            wait_time += self.calculate_charging_time(req.requested_amount, pile.power)

        # 计算自己的充电时间
        charging_time = self.calculate_charging_time(request.requested_amount, pile.power)

        # 返回完成充电所需总时长
        return wait_time + charging_time

    def assign_charging_pile(self, request: ChargingRequest) -> ChargingPile:
        """为充电请求分配充电桩"""
        available_piles = self.get_available_piles(request.charging_mode)
        
        if not available_piles:
            return None

        # 计算每个可用充电桩的总充电时间（等待时间+自己充电时间）
        pile_times = {}
        for pile in available_piles:
            total_time = self.calculate_total_charging_time(request, pile)
            pile_times[pile] = total_time
            print(f"充电桩 {pile.pile_number} 完成时间估计: {total_time}小时")

        # 选择总充电时间最短的充电桩
        best_pile = min(pile_times.items(), key=lambda x: x[1])[0]
        print(f"选择充电桩 {best_pile.pile_number} (所需时长最短: {pile_times[best_pile]}小时)")
        
        # 查询充电桩当前队列中的请求数
        queue_requests = self.db.query(ChargingRequest).filter(
            ChargingRequest.charging_pile_id == best_pile.id,
            ChargingRequest.status.in_(["charging", "waiting"])
        ).all()
        
        # 检查充电桩是否已有正在充电的请求
        charging_requests = [req for req in queue_requests if req.status == "charging"]
        
        # 确定请求状态
        if not charging_requests:
            # 如果没有车辆在充电，这辆车可以直接充电
            request.status = "charging"
            request.started_at = datetime.now()
            best_pile.status = ChargingPileStatus.OCCUPIED
            self.db.commit()  # 立即提交状态更改
            print(f"充电桩 {best_pile.pile_number} 状态更新为占用(OCCUPIED)")
        else:
            # 已有车辆在充电，这辆车需要等待
            request.status = "waiting"
            request.started_at = None
        
        # 分配充电桩ID
        request.charging_pile_id = best_pile.id
        self.db.commit()
        
        return best_pile

    def allow_simultaneous_charging(self, user_id: int) -> bool:
        """检查是否允许用户同时使用多个充电桩"""
        # 获取用户当前正在充电的请求数
        active_charges = self.db.query(ChargingRequest).filter(
            ChargingRequest.user_id == user_id,
            ChargingRequest.status == "charging"
        ).count()
        
        # 默认不允许同时充电
        return False

    def handle_fault_pile(self, fault_pile: ChargingPile):
        """处理故障充电桩"""
        # 获取故障充电桩队列中的所有请求（充电中和等待中的）
        queue_requests = self.db.query(ChargingRequest).filter(
            ChargingRequest.charging_pile_id == fault_pile.id,
            ChargingRequest.status.in_(["charging", "waiting"])
        ).all()

        # 重新调度队列中的请求
        for request in queue_requests:
            new_pile = self.assign_charging_pile(request)
            if new_pile:
                request.charging_pile_id = new_pile.id
                # 状态在assign_charging_pile方法中已设置
                self.db.commit() 

    def handle_charging_completion(self, pile: ChargingPile):
        """处理充电完成后的状态更新"""
        # 获取该充电桩等待队列中的车辆，按照创建时间排序
        waiting_requests = self.db.query(ChargingRequest).filter(
            ChargingRequest.charging_pile_id == pile.id,
            ChargingRequest.status == "waiting"
        ).order_by(ChargingRequest.created_at).all()
        
        if waiting_requests:
            # 取队列中第一辆等待的车开始充电
            next_request = waiting_requests[0]
            next_request.status = "charging"
            next_request.started_at = datetime.now()
            # 确保充电桩状态为占用
            pile.status = ChargingPileStatus.OCCUPIED
            self.db.commit()
            print(f"充电桩 {pile.pile_number} 开始为下一辆车 {next_request.queue_number} 充电，状态为占用")
        else:
            # 检查是否还有其他正在充电的请求
            charging_requests = self.db.query(ChargingRequest).filter(
                ChargingRequest.charging_pile_id == pile.id,
                ChargingRequest.status == "charging"
            ).all()
            
            if not charging_requests:
                # 如果没有等待的车辆且没有正在充电的车辆，将充电桩状态设为可用
                pile.status = ChargingPileStatus.AVAILABLE
                self.db.commit()
                print(f"充电桩 {pile.pile_number} 当前无车辆使用，状态设为可用")
            else:
                # 如果还有其他车辆在充电，保持占用状态
                pile.status = ChargingPileStatus.OCCUPIED
                self.db.commit()
                print(f"充电桩 {pile.pile_number} 仍有其他车辆在充电，保持占用状态") 