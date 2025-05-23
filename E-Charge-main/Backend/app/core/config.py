from pydantic import BaseModel
import os

class Settings(BaseModel):
    # 数据库配置
    DATABASE_URL: str = "sqlite:///./charging_station.db"
    
    # JWT配置
    SECRET_KEY: str = "your-secret-key-here"  # 在生产环境中应该使用环境变量
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # 系统配置参数
    # 等候区容量设置 (注: 这与WaitingAreaSize参数相同，为保持兼容性保留)
    FAST_QUEUE_CAPACITY: int = int(os.getenv("FAST_QUEUE_CAPACITY", "6"))
    TRICKLE_QUEUE_CAPACITY: int = int(os.getenv("TRICKLE_QUEUE_CAPACITY", "6"))
    
    # 可配置参数 (验收测试时可自由设置)
    # 快充电桩数量
    FAST_CHARGING_PILE_NUM: int = int(os.getenv("FAST_CHARGING_PILE_NUM", "2"))
    # 慢充电桩数量
    TRICKLE_CHARGING_PILE_NUM: int = int(os.getenv("TRICKLE_CHARGING_PILE_NUM", "3"))
    # 等候区车位容量 (与FAST_QUEUE_CAPACITY和TRICKLE_QUEUE_CAPACITY配合使用)
    WAITING_AREA_SIZE: int = int(os.getenv("WAITING_AREA_SIZE", "6"))
    # 充电桩排队队列长度
    CHARGING_QUEUE_LEN: int = int(os.getenv("CHARGING_QUEUE_LEN", "2"))
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 确保等候区容量一致
        if "WAITING_AREA_SIZE" in os.environ:
            self.FAST_QUEUE_CAPACITY = self.WAITING_AREA_SIZE
            self.TRICKLE_QUEUE_CAPACITY = self.WAITING_AREA_SIZE

settings = Settings() 