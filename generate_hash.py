# pyrefly: ignore [missing-import]
from backend.app.core.auth_utils import hash_password

# Apna password yahan enter karein
plain_password = "[password123!]"

hashed = hash_password(plain_password)
print("Generated Hash:", hashed)