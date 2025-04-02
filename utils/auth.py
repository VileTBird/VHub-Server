import os
import json
import hashlib
import secrets
from datetime import datetime, timedelta
import jwt

SECRET_KEY_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'secret_key.txt')

def get_secret_key():
    """Get the secret key, creating it if necessary."""
    if os.path.exists(SECRET_KEY_FILE):
        with open(SECRET_KEY_FILE, 'r') as f:
            return f.read().strip()
    else:
        secret_key = secrets.token_hex(32)
        os.makedirs(os.path.dirname(SECRET_KEY_FILE), exist_ok=True)
        with open(SECRET_KEY_FILE, 'w') as f:
            f.write(secret_key)
        return secret_key

SECRET_KEY = get_secret_key()

def hash_password(password):
    """Hash a password for storage."""
    salt = secrets.token_hex(8)
    pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), 
                                  salt.encode('utf-8'), 100000)
    pwdhash = pwdhash.hex()
    return f"{salt}${pwdhash}"

def verify_password(stored_password, provided_password):
    """Verify a password against its hash."""
    salt, hash = stored_password.split('$')
    pwdhash = hashlib.pbkdf2_hmac('sha256', provided_password.encode('utf-8'), 
                                  salt.encode('utf-8'), 100000)
    return pwdhash.hex() == hash

def create_token(user_id, expires_in=24):
    """Create a JWT token for a user."""
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(hours=expires_in),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

def verify_token(token):
    """Verify a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return {'error': 'Token expired'}
    except jwt.InvalidTokenError:
        return {'error': 'Invalid token'}