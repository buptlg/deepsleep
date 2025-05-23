from app.core.database import SessionLocal
from app.models.models import User

def check_users():
    db = SessionLocal()
    try:
        # 查询所有用户
        users = db.query(User).all()
        
        print(f"\n当前数据库中共有 {len(users)} 个用户:")
        print("-" * 50)
        
        for user in users:
            print(f"ID: {user.id}")
            print(f"用户名: {user.username}")
            print(f"是否管理员: {'是' if user.is_admin else '否'}")
            print(f"是否激活: {'是' if user.is_active else '否'}")
            print("-" * 50)
            
    except Exception as e:
        print(f"查询用户时出错: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_users() 