import bcrypt

def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

password = "admin123"
hashed = get_password_hash(password)
print(f"Password: {password}")
print(f"Hash: {hashed}")
print(f"Verify: {verify_password(password, hashed)}")

# Test with the hash from debug log
debug_hash = "$2b$12$1p6AKeCmGbEftcp96xuOReRFohhk/LDSGQHFua8HvdrVbiaijDWO."
print(f"Verify debug hash: {verify_password(password, debug_hash)}")
