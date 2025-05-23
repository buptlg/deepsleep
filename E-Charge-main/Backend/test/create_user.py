from app.core.database import SessionLocal
from app.models.models import User
from app.core.security import get_password_hash

def create_admin_user():
    db = SessionLocal()
    try:
        # 检查用户是否已存在
        admin_user = db.query(User).filter(User.username == "admin").first()
        if admin_user:
            print("管理员用户已存在")
            return
        
        # 创建管理员用户
        admin = User(
            username="admin",
            hashed_password=get_password_hash("admin123"),
            is_active=True,
            is_admin=True
        )
        db.add(admin)
        
        # 创建普通用户
        normal_user = User(
            username="user",
            hashed_password=get_password_hash("user123"),
            is_active=True,
            is_admin=False
        )
        db.add(normal_user)
        
        db.commit()
        print("用户创建成功!")
        print("管理员账号: admin 密码: admin123")
        print("普通用户账号: user 密码: user123")
    except Exception as e:
        print(f"创建用户时出错: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_admin_user() 