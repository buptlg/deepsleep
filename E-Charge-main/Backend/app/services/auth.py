from sqlalchemy.orm import Session
from ..models.models import User
from ..core.security import verify_password
from fastapi import HTTPException, status

def authenticate_user(db: Session, username: str, password: str):
    """验证用户"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="账户不存在",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user 