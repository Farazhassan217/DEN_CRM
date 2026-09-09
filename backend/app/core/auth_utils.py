import bcrypt

def hash_password(password: str) -> str:
    """Hash a password using bcrypt directly to avoid passlib backend bugs"""
    # Ensure password is encoded to bytes and truncate to 72 bytes max
    pwd_bytes = password.encode('utf-8')[:72]
    # Generate salt and hash
    hashed = bcrypt.hashpw(pwd_bytes, bcrypt.gensalt())
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password"""
    pwd_bytes = plain_password.encode('utf-8')[:72]
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(pwd_bytes, hashed_bytes)