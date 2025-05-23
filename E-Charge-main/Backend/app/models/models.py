from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import enum

Base = declarative_base()

class ChargingMode(enum.Enum):
    FAST = "fast"
    TRICKLE = "trickle"

class ChargingPileStatus(enum.Enum):
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    FAULT = "fault"
    MAINTENANCE = "maintenance"
    CLOSED = "closed"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    
    # 添加关系
    vehicles = relationship("Vehicle", back_populates="user")
    charging_requests = relationship("ChargingRequest", back_populates="user")

class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    battery_capacity = Column(Float)  # 电池总容量（度）
    current_battery = Column(Float)   # 当前电量（度）
    user = relationship("User", back_populates="vehicles")
    charging_requests = relationship("ChargingRequest", back_populates="vehicle")

class ChargingPile(Base):
    __tablename__ = "charging_piles"

    id = Column(Integer, primary_key=True, index=True)
    pile_number = Column(String, unique=True, index=True)  # 充电桩编号
    charging_mode = Column(Enum(ChargingMode))
    status = Column(Enum(ChargingPileStatus), default=ChargingPileStatus.AVAILABLE)
    power = Column(Float)  # 充电功率（度/小时）
    total_charging_times = Column(Integer, default=0)
    total_charging_duration = Column(Float, default=0.0)  # 总充电时长（小时）
    total_charging_amount = Column(Float, default=0.0)    # 总充电量（度）
    
    # 添加关系
    charging_requests = relationship("ChargingRequest", back_populates="charging_pile")
    charging_details = relationship("ChargingDetail", back_populates="charging_pile")

class ChargingRequest(Base):
    __tablename__ = "charging_requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"))
    queue_number = Column(String, unique=True, index=True)  # 排队号码
    charging_mode = Column(Enum(ChargingMode))
    requested_amount = Column(Float)  # 请求充电量（度）
    status = Column(String)  # 状态：waiting, charging, completed, cancelled
    created_at = Column(DateTime)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    charging_pile_id = Column(Integer, ForeignKey("charging_piles.id"), nullable=True)
    
    # 添加关系
    user = relationship("User", back_populates="charging_requests")
    vehicle = relationship("Vehicle", back_populates="charging_requests")
    charging_pile = relationship("ChargingPile", back_populates="charging_requests")
    charging_details = relationship("ChargingDetail", back_populates="request")

class ChargingDetail(Base):
    __tablename__ = "charging_details"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("charging_requests.id"))
    charging_pile_id = Column(Integer, ForeignKey("charging_piles.id"))
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    charging_amount = Column(Float)  # 实际充电量（度）
    charging_duration = Column(Float)  # 充电时长（小时）
    electricity_fee = Column(Float)  # 充电费用
    service_fee = Column(Float)  # 服务费用
    total_fee = Column(Float)  # 总费用
    
    # 添加关系
    request = relationship("ChargingRequest", back_populates="charging_details")
    charging_pile = relationship("ChargingPile", back_populates="charging_details") 