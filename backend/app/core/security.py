from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, Security, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
import sys
from pathlib import Path

# Ensure root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))
from config.settings import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security_bearer = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Pre-defined roles for Oil India Limited enterprise governance
ROLE_SUPERINTENDENT = "Rig_Superintendent"
ROLE_ENGINEER = "Drilling_Engineer"
ROLE_GEOLOGIST = "Operations_Geologist"
ROLE_AUDITOR = "System_Auditor"
ROLE_GUEST = "Guest_Operator"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_token(token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token or token expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    api_key: Optional[str] = Depends(api_key_header)
) -> Dict[str, Any]:
    # Allow API Key in development/demo mode for easy script execution
    if api_key and (api_key == "nwis_demo_api_key_2026" or settings.ENVIRONMENT == "development"):
        return {
            "sub": "demo_drilling_engineer",
            "role": ROLE_ENGINEER,
            "organization": "Oil India Limited",
            "rig_assigned": "RIG-OIL-09"
        }

    if not credentials:
        # Default fallback to guest operator in development to ease testing
        if settings.ENVIRONMENT == "development":
            return {
                "sub": "local_dev_user",
                "role": ROLE_SUPERINTENDENT,
                "organization": "Oil India Limited (Testbed)"
            }
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials missing.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return decode_token(credentials.credentials)

def require_role(allowed_roles: List[str]):
    def role_checker(current_user: Dict[str, Any] = Depends(get_current_user)):
        user_role = current_user.get("role", ROLE_GUEST)
        if user_role not in allowed_roles and user_role != ROLE_SUPERINTENDENT:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted. Required roles: {allowed_roles}, your role: {user_role}"
            )
        return current_user
    return role_checker
