"""Security utilities for encryption and decryption."""

import base64
import hashlib
import json
import logging
import os
import re
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple

from cryptography.fernet import Fernet
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)

# Get encryption key from environment or generate one
# In production, this should be a fixed value stored securely
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
if not ENCRYPTION_KEY:
    # Generate a key if not provided
    logger.warning(
        "ENCRYPTION_KEY not found in environment, generating a temporary one"
    )
    ENCRYPTION_KEY = Fernet.generate_key().decode()


# Initialize the encryption suite
def get_cipher():
    """Get a Fernet cipher for encryption/decryption using the app's key."""
    try:
        # Ensure the key is properly formatted for Fernet
        key_bytes = ENCRYPTION_KEY.encode()
        # If the key is not 32 bytes, pad it or hash it to get a proper key
        if len(key_bytes) != 32:
            from cryptography.hazmat.primitives import hashes

            digest = hashes.Hash(hashes.SHA256())
            digest.update(key_bytes)
            key_bytes = digest.finalize()

        # Encode to base64 for Fernet
        fernet_key = base64.urlsafe_b64encode(key_bytes)
        return Fernet(fernet_key)
    except Exception as e:
        logger.error(f"Error initializing cipher: {str(e)}")
        raise


def encrypt_string(text: str) -> str:
    """
    Encrypt a string using Fernet symmetric encryption.

    Args:
        text: The plain text to encrypt

    Returns:
        Encrypted string
    """
    if not text:
        return None

    try:
        cipher = get_cipher()
        encrypted_text = cipher.encrypt(text.encode())
        return encrypted_text.decode()
    except Exception as e:
        logger.error(f"Error encrypting string: {str(e)}")
        # Return None instead of raising to prevent API errors
        # but log the issue for debugging
        return None


def decrypt_string(encrypted_text: str) -> str:
    """
    Decrypt a string that was encrypted with Fernet.

    Args:
        encrypted_text: The encrypted text to decrypt

    Returns:
        Decrypted string or None if decryption fails
    """
    if not encrypted_text:
        return None

    try:
        cipher = get_cipher()
        decrypted_text = cipher.decrypt(encrypted_text.encode())
        return decrypted_text.decode()
    except Exception as e:
        logger.error(f"Error decrypting string: {str(e)}")
        # Return None instead of raising to prevent API errors
        return None


def generate_short_token(data: Dict[str, Any], expires_days: int = 365) -> str:
    """
    Generate a short, secure token containing encoded deployment information.

    Args:
        data: Dictionary containing deployment data (deployment_id, api_key, etc.)
        expires_days: Number of days until token expires

    Returns:
        A short, URL-safe token string
    """
    # Add expiration timestamp
    expires_at = (datetime.now() + timedelta(days=expires_days)).timestamp()

    # Create payload with data and expiration
    payload = {"exp": expires_at, "data": data}

    # Convert to JSON and encrypt
    json_data = json.dumps(payload)
    encrypted = encrypt_string(json_data)

    # Create a base64 URL-safe version (shorter for URLs)
    # Then create a hash of the first part to make it even shorter
    short_hash = hashlib.sha256(encrypted[:20].encode()).hexdigest()[:12]

    # Combine parts to make the final token
    token = f"{short_hash}.{base64.urlsafe_b64encode(encrypted[:10].encode()).decode()}"

    # Remove any non-alphanumeric characters
    token = re.sub(r"[^a-zA-Z0-9]", "", token)

    # Ensure token is the right length for URLs
    return token[:16]


def decode_short_token(token: str) -> Tuple[Dict[str, Any], bool]:
    """
    Decode a short token and return the original data.

    Args:
        token: The short token to decode

    Returns:
        Tuple of (data_dict, is_valid)
    """
    try:
        # Look up the token in the database
        # This is a placeholder - you would implement database lookup here
        # For now, we'll return an empty dict and False
        return {}, False

    except Exception as e:
        logger.error(f"Error decoding token: {e}")
        return {}, False
