import sqlite3

def check_database_schema():
    # 连接数据库
    conn = sqlite3.connect("charging_station.db")
    cursor = conn.cursor()
    
    # 获取所有表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print("\n数据库中的表:")
    print("-" * 50)
    for table in tables:
        table_name = table[0]
        print(f"表名: {table_name}")
        
        # 获取表结构
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        
        print("列结构:")
        for column in columns:
            col_id, col_name, col_type, not_null, default_val, pk = column
            print(f"  - {col_name} ({col_type})")
            
        # 如果是users表，获取数据内容
        if table_name == 'users':
            cursor.execute(f"SELECT * FROM {table_name};")
            rows = cursor.fetchall()
            
            print(f"\n用户表数据 ({len(rows)} 条记录):")
            for row in rows:
                print(f"  用户ID: {row[0]}")
                print(f"  用户名: {row[1]}")
                print(f"  密码哈希: {row[3][:20]}... (已截断)")
                print(f"  是否激活: {row[4]}")
                print(f"  是否管理员: {row[5]}")
                print("  " + "-" * 30)
        
        print("-" * 50)
    
    # 关闭连接
    conn.close()

if __name__ == "__main__":
    check_database_schema() 