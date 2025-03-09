import os
import logging
from typing import Dict, Optional
from datetime import datetime, timedelta
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# OAuth2 configuration
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# User model
class User(BaseModel):
    username: str
    full_name: Optional[str] = None
    permissions: Dict[str, bool] = {}
    disabled: Optional[bool] = None

# Token model
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# In-memory user DB (replace with a real DB in production)
USERS_DB = {
    "admin": {
        "username": "admin",
        "full_name": "Admin User",
        "password": "admin123",  # Store hashed passwords in production!
        "permissions": {
            "zoom": True,
            "gmail": True,
            "notion": True,
            "salesforce": True
        },
        "disabled": False
    },
    "sales": {
        "username": "sales",
        "full_name": "Sales User",
        "password": "sales123",  # Store hashed passwords in production!
        "permissions": {
            "zoom": True,
            "gmail": True,
            "notion": True,
            "salesforce": True
        },
        "disabled": False
    }
}

class AuthService:
    """Service for handling authentication and authorization"""
    
    def __init__(self):
        self.secret_key = os.getenv("SECRET_KEY", "your_secret_key_here")
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 60
    
    def verify_user(self, username: str, password: str) -> Optional[User]:
        """Verify username and password"""
        if username not in USERS_DB:
            return None
        
        user_dict = USERS_DB[username]
        
        # In production, use proper password hashing and verification
        if user_dict["password"] != password:
            return None
            
        if user_dict.get("disabled", False):
            return None
            
        return User(**user_dict)
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
            
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    async def get_current_user(self, token: str = Depends(oauth2_scheme)) -> User:
        """Validate token and get current user"""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            username: str = payload.get("sub")
            if username is None:
                raise credentials_exception
                
            token_data = TokenData(username=username)
        except JWTError:
            raise credentials_exception
            
        user_dict = USERS_DB.get(token_data.username)
        if user_dict is None:
            raise credentials_exception
            
        return User(**user_dict)
    
    async def get_current_active_user(self, current_user: User = Depends(get_current_user)) -> User:
        """Check if user is active"""
        if current_user.disabled:
            raise HTTPException(status_code=400, detail="Inactive user")
        return current_user
        
    def check_permission(self, user: User, source: str) -> bool:
        """Check if user has permission to access a specific data source"""
        if not user or not source:
            return False
            
        # Admin has access to everything
        if user.username == "admin":
            return True
            
        # Check specific permissions
        return user.permissions.get(source, False) 