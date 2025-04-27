"""Security utilities for encryption and decryption."""
import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv
import base64
import logging

# Load environment variables
load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)

# Get encryption key from environment or generate one
# In production, this should be a fixed value stored securely
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
if not ENCRYPTION_KEY:
    # Generate a key if not provided
    logger.warning("ENCRYPTION_KEY not found in environment, generating a temporary one")
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