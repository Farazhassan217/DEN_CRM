import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple
from uuid import UUID
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from ..core.config import settings
from ..core.roles import UserRole
from ..core.redis_client import redis_client
from ..schemas.user import TokenData, User
from ..models.user import UserModel
from ..core.auth_utils import verify_password as _verify_password

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer security scheme
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def is_token_revoked(jti: str) -> bool:
    """Check if token's jti is in the Redis revocation list."""
    if not jti:
        return False
    return redis_client.exists(f"revoked:jti:{jti}")


def revoke_token(token: str) -> bool:
    """
    Revoke a JWT token by storing its jti in Redis until expiration.
    Returns True if successfully revoked.
    """
    try:
        # Decode without verifying signature to handle near-expiration
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={"verify_exp": False}
        )
        jti = payload.get("jti")
        exp = payload.get("exp")
        if not jti:
            return False

        # Calculate remaining lifetime
        now = datetime.now(timezone.utc).timestamp()
        ttl = int(exp - now) if exp else 3600
        if ttl <= 0:
            ttl = 60  # Keep briefly even if already expired

        return redis_client.set(f"revoked:jti:{jti}", "revoked", ex=ttl)
    except Exception:
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token with unique jti and token_type"""
    to_encode = data.copy()
    
    for key, value in to_encode.items():
        if isinstance(value, UUID):
            to_encode[key] = str(value)
    
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    jti = str(uuid.uuid4())
    to_encode.update({
        "exp": expire,
        "jti": jti,
        "token_type": "access"
    })
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT refresh token with 7-day default expiration and token_type='refresh'"""
    to_encode = data.copy()
    
    for key, value in to_encode.items():
        if isinstance(value, UUID):
            to_encode[key] = str(value)
            
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
    jti = str(uuid.uuid4())
    to_encode.update({
        "exp": expire,
        "jti": jti,
        "token_type": "refresh"
    })
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[TokenData]:
    """Decode and validate a JWT access token, verifying it is not revoked"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        jti = payload.get("jti")
        token_type = payload.get("token_type", "access")
        
        # Ensure it is an access token
        if token_type != "access":
            return None
            
        # Check revocation
        if jti and is_token_revoked(jti):
            return None

        user_id: str = payload.get("sub")
        email: str = payload.get("email")
        role: str = payload.get("role")
        org_id: str = payload.get("organization_id")
        clinics: list = payload.get("assigned_clinics", [])
        
        if user_id is None or email is None:
            return None
        
        return TokenData(
            user_id=user_id,
            email=email,
            role=UserRole(role) if role else None,
            organization_id=org_id,
            assigned_clinics=clinics,
            jti=jti,
            token_type=token_type
        )
    except JWTError:
        return None


def decode_refresh_token(token: str) -> Optional[TokenData]:
    """Decode and validate a JWT refresh token, verifying it is not revoked"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        jti = payload.get("jti")
        token_type = payload.get("token_type")

        # Must strictly be a refresh token
        if token_type != "refresh":
            return None

        # Check revocation
        if jti and is_token_revoked(jti):
            return None

        user_id: str = payload.get("sub")
        email: str = payload.get("email")
        role: str = payload.get("role")
        org_id: str = payload.get("organization_id")
        clinics: list = payload.get("assigned_clinics", [])

        if user_id is None or email is None:
            return None

        return TokenData(
            user_id=user_id,
            email=email,
            role=UserRole(role) if role else None,
            organization_id=org_id,
            assigned_clinics=clinics,
            jti=jti,
            token_type=token_type
        )
    except JWTError:
        return None


async def get_current_user(auth_credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get the current authenticated user from JWT token and verify revocation"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials or token has been revoked",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = auth_credentials.credentials
    token_data = decode_access_token(token)
    if token_data is None:
        raise credentials_exception
    
    user = await UserModel.get_by_id(token_data.user_id)
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )
    
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get the current active user"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_current_super_admin(current_user: User = Depends(get_current_user)) -> User:
    """Get the current user and verify they are a super admin"""
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Super admin required."
        )
    return current_user


class AuthService:
    """Authentication service"""
    
    @staticmethod
    async def authenticate_user(email: str, password: str) -> Optional[User]:
        clean_email = email.lower().strip() if email else ""
        user_with_pwd = await UserModel.get_by_email_with_password(clean_email)

        if not user_with_pwd or not user_with_pwd.password:
            return None

        if not _verify_password(password, user_with_pwd.password):
            return None

        return await UserModel.get_by_id(str(user_with_pwd.id))
    
    @staticmethod
    async def login(email: str, password: str) -> Tuple[User, str, str]:
        """Login user and return user + access token + refresh token"""
        user = await AuthService.authenticate_user(email, password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated"
            )
        
        payload_data = {
            "sub": user.id,
            "email": user.email,
            "role": user.role.value if hasattr(user.role, "value") else user.role,
            "organization_id": user.organization_id,
            "assigned_clinics": user.assigned_clinics or []
        }
        
        access_token = create_access_token(data=payload_data)
        refresh_token = create_refresh_token(data=payload_data)
        
        return user, access_token, refresh_token

    @staticmethod
    async def rotate_tokens(old_refresh_token: str) -> Tuple[str, str, User]:
        """Validate old refresh token, revoke it, and issue new access & refresh tokens"""
        token_data = decode_refresh_token(old_refresh_token)
        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )

        user = await UserModel.get_by_id(str(token_data.user_id))
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account not found or deactivated"
            )

        # Revoke the old refresh token (Token Rotation)
        revoke_token(old_refresh_token)

        payload_data = {
            "sub": user.id,
            "email": user.email,
            "role": user.role.value if hasattr(user.role, "value") else user.role,
            "organization_id": user.organization_id,
            "assigned_clinics": user.assigned_clinics or []
        }

        new_access_token = create_access_token(data=payload_data)
        new_refresh_token = create_refresh_token(data=payload_data)

        return new_access_token, new_refresh_token, user