import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime
from ..app.main import app
from ..app.core.database import get_db, Base, engine
from ..app.models.models import User
from ..app.core.security import get_password_hash

# 创建测试数据库
Base.metadata.create_all(bind=engine)

# 创建测试客户端
client = TestClient(app)

# 测试数据
test_user = {
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpassword123"
}

test_admin = {
    "username": "admin",
    "email": "admin@example.com",
    "password": "adminpassword123",
    "is_admin": True
}

def get_test_db():
    """获取测试数据库会话"""
    db = Session(engine)
    try:
        yield db
    finally:
        db.close()

# 覆盖依赖
app.dependency_overrides[get_db] = get_test_db

@pytest.fixture(autouse=True)
def setup_database():
    """每个测试前清理数据库"""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_create_user():
    """测试用户注册"""
    response = client.post("/api/users/register", json=test_user)
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == test_user["username"]
    assert data["email"] == test_user["email"]
    assert "id" in data
    assert "hashed_password" not in data

def test_create_duplicate_username():
    """测试重复用户名注册"""
    # 先创建一个用户
    client.post("/api/users/register", json=test_user)
    
    # 尝试使用相同的用户名注册
    response = client.post("/api/users/register", json=test_user)
    assert response.status_code == 400
    assert response.json()["detail"] == "用户名已存在"

def test_create_duplicate_email():
    """测试重复邮箱注册"""
    # 先创建一个用户
    client.post("/api/users/register", json=test_user)
    
    # 尝试使用相同的邮箱注册
    duplicate_user = test_user.copy()
    duplicate_user["username"] = "anotheruser"
    response = client.post("/api/users/register", json=duplicate_user)
    assert response.status_code == 400
    assert response.json()["detail"] == "邮箱已存在"

def test_login():
    """测试用户登录"""
    # 先创建用户
    client.post("/api/users/register", json=test_user)
    
    # 测试登录
    response = client.post("/api/token", data={
        "username": test_user["username"],
        "password": test_user["password"]
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_wrong_password():
    """测试错误密码登录"""
    # 先创建用户
    client.post("/api/users/register", json=test_user)
    
    # 使用错误密码登录
    response = client.post("/api/token", data={
        "username": test_user["username"],
        "password": "wrongpassword"
    })
    assert response.status_code == 401

def test_get_user_info():
    """测试获取用户信息"""
    # 先创建用户并登录
    client.post("/api/users/register", json=test_user)
    login_response = client.post("/api/token", data={
        "username": test_user["username"],
        "password": test_user["password"]
    })
    token = login_response.json()["access_token"]
    
    # 获取用户信息
    response = client.get("/api/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == test_user["username"]
    assert data["email"] == test_user["email"]

def test_update_user_info():
    """测试更新用户信息"""
    # 先创建用户并登录
    client.post("/api/users/register", json=test_user)
    login_response = client.post("/api/token", data={
        "username": test_user["username"],
        "password": test_user["password"]
    })
    token = login_response.json()["access_token"]
    
    # 更新用户信息
    update_data = {
        "email": "newemail@example.com",
        "password": "newpassword123"
    }
    response = client.put("/api/users/me", 
                         json=update_data,
                         headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == update_data["email"]
    
    # 验证新密码可以登录
    login_response = client.post("/api/token", data={
        "username": test_user["username"],
        "password": update_data["password"]
    })
    assert login_response.status_code == 200

def test_admin_access():
    """测试管理员访问其他用户信息"""
    # 创建普通用户
    client.post("/api/users/register", json=test_user)
    
    # 创建管理员用户
    admin_response = client.post("/api/users/register", json=test_admin)
    admin_id = admin_response.json()["id"]
    
    # 管理员登录
    login_response = client.post("/api/token", data={
        "username": test_admin["username"],
        "password": test_admin["password"]
    })
    token = login_response.json()["access_token"]
    
    # 管理员访问普通用户信息
    response = client.get(f"/api/users/{admin_id}", 
                         headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200

def test_non_admin_access():
    """测试非管理员访问其他用户信息"""
    # 创建两个普通用户
    client.post("/api/users/register", json=test_user)
    user2 = test_user.copy()
    user2["username"] = "user2"
    user2["email"] = "user2@example.com"
    user2_response = client.post("/api/users/register", json=user2)
    user2_id = user2_response.json()["id"]
    
    # 第一个用户登录
    login_response = client.post("/api/token", data={
        "username": test_user["username"],
        "password": test_user["password"]
    })
    token = login_response.json()["access_token"]
    
    # 尝试访问其他用户信息
    response = client.get(f"/api/users/{user2_id}", 
                         headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403 