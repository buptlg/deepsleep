from sqlalchemy.orm import Session
from ..core.config import settings
from ..models.models import ChargingPile, ChargingMode, ChargingPileStatus

class InitializationService:
    """
    系统初始化服务
    用于根据系统配置自动创建充电桩和初始化系统设置
    """
    
    @staticmethod
    def initialize_charging_piles(db: Session):
        """初始化系统充电桩"""
        
        # 检查是否已有充电桩数据
        existing_piles = db.query(ChargingPile).all()
        if existing_piles:
            # 如果已有充电桩数据，更新其状态
            for pile in existing_piles:
                pile.status = ChargingPileStatus.AVAILABLE
            db.commit()
            
            # 数量变更处理
            fast_piles = [p for p in existing_piles if p.charging_mode == ChargingMode.FAST]
            trickle_piles = [p for p in existing_piles if p.charging_mode == ChargingMode.TRICKLE]
            
            # 如果配置的数量与现有数量不一致，进行调整
            # 创建快充电桩
            if len(fast_piles) < settings.FAST_CHARGING_PILE_NUM:
                # 需要增加快充电桩
                # 使用A、B命名快充电桩
                pile_names = ['A', 'B']
                for i in range(len(fast_piles), settings.FAST_CHARGING_PILE_NUM):
                    pile_name = pile_names[i]
                    db.add(ChargingPile(
                        pile_number=pile_name,
                        charging_mode=ChargingMode.FAST,
                        status=ChargingPileStatus.AVAILABLE,
                        power=30.0  # 快充功率30度/小时
                    ))
            
            # 创建慢充电桩
            if len(trickle_piles) < settings.TRICKLE_CHARGING_PILE_NUM:
                # 需要增加慢充电桩
                # 使用C、D、E命名慢充电桩
                pile_names = ['C', 'D', 'E']
                for i in range(len(trickle_piles), settings.TRICKLE_CHARGING_PILE_NUM):
                    pile_name = pile_names[i]
                    db.add(ChargingPile(
                        pile_number=pile_name,
                        charging_mode=ChargingMode.TRICKLE,
                        status=ChargingPileStatus.AVAILABLE,
                        power=7.0  # 慢充功率7度/小时
                    ))
                    
            db.commit()
            return
            
        # 创建快充电桩
        # 使用A、B命名快充电桩
        pile_names = ['A', 'B']
        for i in range(min(settings.FAST_CHARGING_PILE_NUM, len(pile_names))):
            db.add(ChargingPile(
                pile_number=pile_names[i],
                charging_mode=ChargingMode.FAST,
                status=ChargingPileStatus.AVAILABLE,
                power=30.0  # 快充功率30度/小时
            ))
        
        # 创建慢充电桩
        # 使用C、D、E命名慢充电桩
        pile_names = ['C', 'D', 'E']
        for i in range(min(settings.TRICKLE_CHARGING_PILE_NUM, len(pile_names))):
            db.add(ChargingPile(
                pile_number=pile_names[i],
                charging_mode=ChargingMode.TRICKLE,
                status=ChargingPileStatus.AVAILABLE,
                power=7.0  # 慢充功率7度/小时
            ))
            
        db.commit() 