"""
Security and Cryptography Module.

This module provides utilities for:
1. Secure password hashing and verification using `passlib` with the `bcrypt` algorithm.
2. Generating and validating JSON Web Tokens (JWT) using `python-jose` for session management.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext

from backend.config import settings
from backend.utils.logger import get_logger

# Initialize logger for the security module
logger = get_logger(__name__)

# ==============================================================================
# Configuration Loading
# ==============================================================================
# Load cryptographic settings from the centralized config
SECRET_KEY: str = settings.SECRET_KEY
ALGORITHM: str = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES: int = settings.ACCESS_TOKEN_EXPIRE_MINUTES

# ==============================================================================
# Password Hashing & Verification
# ==============================================================================
# Set up Passlib's CryptContext to use bcrypt as the hashing scheme.
# The deprecated="auto" configuration allows handling outdated hashes if needed.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash a plain-text password using the bcrypt algorithm.
    
    This function takes a raw password string, generates a secure random salt,
    and applies the bcrypt hash function. The resulting string includes the salt
    and the hash in a standard format.
    
    Args:
        password (str): The raw plain-text password to hash.
        
    Returns:
        str: The secure, one-way hashed password.
    """
    logger.info("Hashing password using bcrypt.")
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain-text password against a hashed password.
    
    This function uses passlib's secure comparison helper, which is resistant
    to timing attacks, to check if the plain-text password matches the hash.
    
    Args:
        plain_password (str): The raw password input from the user.
        hashed_password (str): The stored bcrypt hash to compare against.
        
    Returns:
        bool: True if the password matches the hash, False otherwise.
    """
    try:
        # pwd_context.verify automatically extracts the salt from the hash
        # and performs a secure, constant-time comparison.
        match = pwd_context.verify(plain_password, hashed_password)
        if match:
            logger.info("Password verification succeeded.")
        else:
            logger.warning("Password verification failed (mismatch).")
        return match
    except Exception as e:
        logger.error(f"Error during password verification: {e}", exc_info=True)
        return False


# For backwards compatibility with any existing files that might import the old name
def get_password_hash(password: str) -> str:
    """
    Wrapper for hash_password to maintain backwards compatibility.
    
    Args:
        password (str): The raw plain-text password to hash.
        
    Returns:
        str: The secure, one-way hashed password.
    """
    return hash_password(password)


# ==============================================================================
# JWT Token Operations
# ==============================================================================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Generate a cryptographically signed JSON Web Token (JWT) access token.
    
    This token is issued to authenticated users and contains claims (like user ID
    and expiration time). It is signed using the server's SECRET_KEY.
    
    Args:
        data (dict): The dictionary of claims to include in the token payload (e.g., {"sub": user_id}).
        expires_delta (Optional[timedelta]): An optional custom lifetime for the token.
        
    Returns:
        str: The encoded and signed JWT string.
    """
    to_encode = data.copy()
    
    # Calculate the expiration timestamp
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Update the payload with the standard 'exp' (expiration) claim
    to_encode.update({"exp": expire})
    
    try:
        # Encode the token using python-jose
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        logger.info("JWT access token created successfully.")
        return encoded_jwt
    except Exception as e:
        logger.error(f"Failed to generate JWT access token: {e}", exc_info=True)
        raise


def verify_token(token: str) -> Optional[dict]:
    """
    Decode and cryptographically verify a JSON Web Token (JWT).
    
    This function decodes the token, validates its signature against the SECRET_KEY,
    and ensures that the token has not expired.
    
    Args:
        token (str): The signed JWT token string to verify.
        
    Returns:
        Optional[dict]: The decoded payload dictionary if the token is valid,
                        None if the token is expired, invalid, or has a tampered signature.
    """
    try:
        # Decode and verify the token signature and expiration
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        logger.info("JWT token verification succeeded.")
        return payload
    except JWTError as e:
        # JWTError catches expiration (ExpiredSignatureError), invalid signature, etc.
        logger.warning(f"JWT token verification failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during JWT verification: {e}", exc_info=True)
        return None


# For backwards compatibility with existing files (e.g., dependencies.py)
def decode_access_token(token: str) -> Optional[dict]:
    """
    Wrapper for verify_token to maintain backwards compatibility with existing dependencies.
    
    Args:
        token (str): The signed JWT token string to decode.
        
    Returns:
        Optional[dict]: The decoded payload dictionary if valid, None otherwise.
    """
    return verify_token(token)
"""
Security and Cryptography Module.

This module provides utilities for:
1. Secure password hashing and verification using `passlib` with the `bcrypt` algorithm.
2. Generating and validating JSON Web Tokens (JWT) using `python-jose` for session management.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext

from backend.config import settings
from backend.utils.logger import get_logger

# Initialize logger for the security module
logger = get_logger(__name__)

# ==============================================================================
# Configuration Loading
# ==============================================================================
# Load cryptographic settings from the centralized config
SECRET_KEY: str = settings.SECRET_KEY
ALGORITHM: str = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES: int = settings.ACCESS_TOKEN_EXPIRE_MINUTES

# ==============================================================================
# Password Hashing & Verification
# ==============================================================================
# Set up Passlib's CryptContext to use bcrypt as the hashing scheme.
# The deprecated="auto" configuration allows handling outdated hashes if needed.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash a plain-text password using the bcrypt algorithm.
    
    This function takes a raw password string, generates a secure random salt,
    and applies the bcrypt hash function. The resulting string includes the salt
    and the hash in a standard format.
    
    Args:
        password (str): The raw plain-text password to hash.
        
    Returns:
        str: The secure, one-way hashed password.
    """
    logger.info("Hashing password using bcrypt.")
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain-text password against a hashed password.
    
    This function uses passlib's secure comparison helper, which is resistant
    to timing attacks, to check if the plain-text password matches the hash.
    
    Args:
        plain_password (str): The raw password input from the user.
        hashed_password (str): The stored bcrypt hash to compare against.
        
    Returns:
        bool: True if the password matches the hash, False otherwise.
    """
    try:
        # pwd_context.verify automatically extracts the salt from the hash
        # and performs a secure, constant-time comparison.
        match = pwd_context.verify(plain_password, hashed_password)
        if match:
            logger.info("Password verification succeeded.")
        else:
            logger.warning("Password verification failed (mismatch).")
        return match
    except Exception as e:
        logger.error(f"Error during password verification: {e}", exc_info=True)
        return False


# For backwards compatibility with any existing files that might import the old name
def get_password_hash(password: str) -> str:
    """
    Wrapper for hash_password to maintain backwards compatibility.
    
    Args:
        password (str): The raw plain-text password to hash.
        
    Returns:
        str: The secure, one-way hashed password.
    """
    return hash_password(password)


# ==============================================================================
# JWT Token Operations
# ==============================================================================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Generate a cryptographically signed JSON Web Token (JWT) access token.
    
    This token is issued to authenticated users and contains claims (like user ID
    and expiration time). It is signed using the server's SECRET_KEY.
    
    Args:
        data (dict): The dictionary of claims to include in the token payload (e.g., {"sub": user_id}).
        expires_delta (Optional[timedelta]): An optional custom lifetime for the token.
        
    Returns:
        str: The encoded and signed JWT string.
    """
    to_encode = data.copy()
    
    # Calculate the expiration timestamp
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Update the payload with the standard 'exp' (expiration) claim
    to_encode.update({"exp": expire})
    
    try:
        # Encode the token using python-jose
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        logger.info("JWT access token created successfully.")
        return encoded_jwt
    except Exception as e:
        logger.error(f"Failed to generate JWT access token: {e}", exc_info=True)
        raise


def verify_token(token: str) -> Optional[dict]:
    """
    Decode and cryptographically verify a JSON Web Token (JWT).
    
    This function decodes the token, validates its signature against the SECRET_KEY,
    and ensures that the token has not expired.
    
    Args:
        token (str): The signed JWT token string to verify.
        
    Returns:
        Optional[dict]: The decoded payload dictionary if the token is valid,
                        None if the token is expired, invalid, or has a tampered signature.
    """
    try:
        # Decode and verify the token signature and expiration
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        logger.info("JWT token verification succeeded.")
        return payload
    except JWTError as e:
        # JWTError catches expiration (ExpiredSignatureError), invalid signature, etc.
        logger.warning(f"JWT token verification failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during JWT verification: {e}", exc_info=True)
        return None


# For backwards compatibility with existing files (e.g., dependencies.py)
def decode_access_token(token: str) -> Optional[dict]:
    """
    Wrapper for verify_token to maintain backwards compatibility with existing dependencies.
    
    Args:
        token (str): The signed JWT token string to decode.
        
    Returns:
        Optional[dict]: The decoded payload dictionary if valid, None otherwise.
    """
    return verify_token(token)
"""
Security and Cryptography Module.

This module provides utilities for:
1. Secure password hashing and verification using `passlib` with the `bcrypt` algorithm.
2. Generating and validating JSON Web Tokens (JWT) using `python-jose` for session management.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext

from backend.config import settings
from backend.utils.logger import get_logger

# Initialize logger for the security module
logger = get_logger(__name__)

# ==============================================================================
# Configuration Loading
# ==============================================================================
# Load cryptographic settings from the centralized config
SECRET_KEY: str = settings.SECRET_KEY
ALGORITHM: str = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES: int = settings.ACCESS_TOKEN_EXPIRE_MINUTES

# ==============================================================================
# Password Hashing & Verification
# ==============================================================================
# Set up Passlib's CryptContext to use bcrypt as the hashing scheme.
# The deprecated="auto" configuration allows handling outdated hashes if needed.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash a plain-text password using the bcrypt algorithm.
    
    This function takes a raw password string, generates a secure random salt,
    and applies the bcrypt hash function. The resulting string includes the salt
    and the hash in a standard format.
    
    Args:
        password (str): The raw plain-text password to hash.
        
    Returns:
        str: The secure, one-way hashed password.
    """
    logger.info("Hashing password using bcrypt.")
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain-text password against a hashed password.
    
    This function uses passlib's secure comparison helper, which is resistant
    to timing attacks, to check if the plain-text password matches the hash.
    
    Args:
        plain_password (str): The raw password input from the user.
        hashed_password (str): The stored bcrypt hash to compare against.
        
    Returns:
        bool: True if the password matches the hash, False otherwise.
    """
    try:
        # pwd_context.verify automatically extracts the salt from the hash
        # and performs a secure, constant-time comparison.
        match = pwd_context.verify(plain_password, hashed_password)
        if match:
            logger.info("Password verification succeeded.")
        else:
            logger.warning("Password verification failed (mismatch).")
        return match
    except Exception as e:
        logger.error(f"Error during password verification: {e}", exc_info=True)
        return False


# For backwards compatibility with any existing files that might import the old name
def get_password_hash(password: str) -> str:
    """
    Wrapper for hash_password to maintain backwards compatibility.
    
    Args:
        password (str): The raw plain-text password to hash.
        
    Returns:
        str: The secure, one-way hashed password.
    """
    return hash_password(password)


# ==============================================================================
# JWT Token Operations
# ==============================================================================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Generate a cryptographically signed JSON Web Token (JWT) access token.
    
    This token is issued to authenticated users and contains claims (like user ID
    and expiration time). It is signed using the server's SECRET_KEY.
    
    Args:
        data (dict): The dictionary of claims to include in the token payload (e.g., {"sub": user_id}).
        expires_delta (Optional[timedelta]): An optional custom lifetime for the token.
        
    Returns:
        str: The encoded and signed JWT string.
    """
    to_encode = data.copy()
    
    # Calculate the expiration timestamp
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Update the payload with the standard 'exp' (expiration) claim
    to_encode.update({"exp": expire})
    
    try:
        # Encode the token using python-jose
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        logger.info("JWT access token created successfully.")
        return encoded_jwt
    except Exception as e:
        logger.error(f"Failed to generate JWT access token: {e}", exc_info=True)
        raise


def verify_token(token: str) -> Optional[dict]:
    """
    Decode and cryptographically verify a JSON Web Token (JWT).
    
    This function decodes the token, validates its signature against the SECRET_KEY,
    and ensures that the token has not expired.
    
    Args:
        token (str): The signed JWT token string to verify.
        
    Returns:
        Optional[dict]: The decoded payload dictionary if the token is valid,
                        None if the token is expired, invalid, or has a tampered signature.
    """
    try:
        # Decode and verify the token signature and expiration
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        logger.info("JWT token verification succeeded.")
        return payload
    except JWTError as e:
        # JWTError catches expiration (ExpiredSignatureError), invalid signature, etc.
        logger.warning(f"JWT token verification failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during JWT verification: {e}", exc_info=True)
        return None


# For backwards compatibility with existing files (e.g., dependencies.py)
def decode_access_token(token: str) -> Optional[dict]:
    """
    Wrapper for verify_token to maintain backwards compatibility with existing dependencies.
    
    Args:
        token (str): The signed JWT token string to decode.
        
    Returns:
        Optional[dict]: The decoded payload dictionary if valid, None otherwise.
    """
    return verify_token(token)
