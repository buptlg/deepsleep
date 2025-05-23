from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from .core.config import settings
from .core.database import get_db, engine
from .models import Base  # 从 __init__.py 导入 Base
from .models.models import User, Vehicle
from .routers import users, charging, admin
from .core.security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    verify_password,
    get_current_user
)
from .schemas.user import Token
from .services.auth import authenticate_user
from .services.init_service import InitializationService

# 创建数据库表
Base.metadata.create_all(bind=engine)

# 创建默认数据
def create_initial_data():
    db = next(get_db())
    
    # 初始化充电桩
    InitializationService.initialize_charging_piles(db)
    
    # 检查是否已有车辆数据
    vehicle_count = db.query(Vehicle).count()
    if vehicle_count == 0:
        # 为每个用户创建默认车辆
        users = db.query(User).all()
        for user in users:
            if not user.is_admin:  # 只为普通用户创建车辆
                vehicle = Vehicle(
                    user_id=user.id,
                    battery_capacity=60.0,  # 60度电池容量
                    current_battery=30.0    # 当前50%电量
                )
                db.add(vehicle)
        db.commit()

# 尝试创建初始数据
try:
    create_initial_data()
except Exception as e:
    print(f"创建初始数据失败: {e}")

app = FastAPI(
    title="充电站管理系统",
    description="基于FastAPI的充电站管理系统后端API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含路由
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(charging.router, prefix="/api/charging", tags=["charging"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])

@app.post("/api/token")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """用户登录获取令牌"""
    try:
        user = authenticate_user(db, form_data.username, form_data.password)
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}
    except HTTPException as e:
        # 将auth服务中的异常直接向上传递
        raise e

@app.get("/api")
async def root():
    return {"message": "欢迎使用充电站管理系统API"} 