from app.core.database import engine, SessionLocal
from app.models import Base
from app.models.models import User, Vehicle, ChargingPile, ChargingMode, ChargingPileStatus
from app.core.security import get_password_hash
from app.services.init_service import InitializationService

def init_db():
    print("开始初始化数据库...")
    
    # 创建所有表
    print("创建数据库表...")
    Base.metadata.create_all(bind=engine)
    
    # 获取数据库会话
    db = SessionLocal()
    
    try:
        # 检查并创建管理员用户
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            print("创建管理员用户...")
            admin = User(
                username="admin",
                hashed_password=get_password_hash("admin123"),
                is_active=True,
                is_admin=True
            )
            db.add(admin)
            db.commit()
            print("管理员用户创建成功！")
        
        # 检查并创建普通用户
        normal_user = db.query(User).filter(User.username == "user").first()
        if not normal_user:
            print("创建普通用户...")
            user = User(
                username="user",
                hashed_password=get_password_hash("user123"),
                is_active=True,
                is_admin=False
            )
            db.add(user)
            db.commit()
            
            # 为普通用户创建默认车辆
            print("为普通用户创建默认车辆...")
            vehicle = Vehicle(
                user_id=user.id,
                battery_capacity=60.0,  # 60度电池容量
                current_battery=30.0    # 当前50%电量
            )
            db.add(vehicle)
            db.commit()
            print("普通用户和车辆创建成功！")
        
        # 初始化充电桩
        print("初始化充电桩...")
        InitializationService.initialize_charging_piles(db)
        print("充电桩初始化成功！")
        
        print("\n数据库初始化完成！")
        print("管理员账号: admin")
        print("管理员密码: admin123")
        print("普通用户账号: user")
        print("普通用户密码: user123")
        
    except Exception as e:
        print(f"初始化数据库时出错: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_db() 