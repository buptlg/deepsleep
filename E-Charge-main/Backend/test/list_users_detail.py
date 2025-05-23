from app.core.database import SessionLocal
from app.models.models import User
from sqlalchemy import inspect

def inspect_users_table():
    db = SessionLocal()
    try:
        # 获取User模型对应的表结构
        inspector = inspect(db.bind)
        
        # 列出所有表
        tables = inspector.get_table_names()
        print(f"\n数据库中的表: {', '.join(tables)}")
        
        # 获取users表的列
        columns = inspector.get_columns('users')
        print("\n用户表(users)结构:")
        print("-" * 50)
        for column in columns:
            print(f"列名: {column['name']}, 类型: {column['type']}")
        
        # 查询所有用户数据
        users = db.query(User).all()
        print("\n用户数据:")
        print("-" * 50)
        for user in users:
            print(f"ID: {user.id}")
            print(f"用户名: {user.username}")
            print(f"密码哈希: {user.hashed_password[:20]}... (已截断)")
            print(f"是否管理员: {'是' if user.is_admin else '否'}")
            print(f"是否激活: {'是' if user.is_active else '否'}")
            print("-" * 50)
            
    except Exception as e:
        print(f"查询用户表时出错: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    inspect_users_table() 