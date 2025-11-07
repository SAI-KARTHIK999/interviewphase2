"""
PII Vault - Encrypted storage for original PII
Uses AES-GCM authenticated encryption with key versioning.
"""

import os
import json
import base64
import logging
from typing import Optional, Dict, Tuple
from datetime import datetime, timedelta
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from bson import ObjectId

logger = logging.getLogger(__name__)

# Configuration
PII_STORAGE_MODE = os.getenv("PII_STORAGE_MODE", "never_store_original")  # never_store_original, store_encrypted_with_key
VAULT_KEY_VERSION = os.getenv("VAULT_KEY_VERSION", "v1")
VAULT_TTL_DAYS = int(os.getenv("VAULT_TTL_DAYS", "7"))  # Short retention for troubleshooting


class PIIVault:
    """
    Secure vault for storing encrypted PII using AES-GCM.
    """
    
    def __init__(self, key_path: Optional[str] = None):
        """
        Initialize PII vault.
        
        Args:
            key_path: Path to encryption key file. If None, generates ephemeral key.
        """
        self.key_version = VAULT_KEY_VERSION
        self.key = self._load_or_generate_key(key_path)
        self.aesgcm = AESGCM(self.key)
        
        if PII_STORAGE_MODE == "never_store_original":
            logger.info("PII Vault: Mode=never_store_original (encryption disabled)")
        else:
            logger.info(f"PII Vault: Mode={PII_STORAGE_MODE}, KeyVersion={self.key_version}")
    
    def _load_or_generate_key(self, key_path: Optional[str]) -> bytes:
        """
        Load encryption key from file or generate new one.
        
        Args:
            key_path: Path to key file
            
        Returns:
            32-byte encryption key
        """
        if key_path and os.path.exists(key_path):
            try:
                with open(key_path, 'rb') as f:
                    key = f.read()
                if len(key) == 32:
                    logger.info(f"✓ Loaded encryption key from {key_path}")
                    return key
                else:
                    logger.warning(f"Invalid key length in {key_path}, generating new key")
            except Exception as e:
                logger.error(f"Failed to load key from {key_path}: {e}")
        
        # Generate new key
        key = AESGCM.generate_key(bit_length=256)  # 32 bytes
        
        # Try to save it
        if key_path:
            try:
                os.makedirs(os.path.dirname(key_path), exist_ok=True)
                with open(key_path, 'wb') as f:
                    f.write(key)
                os.chmod(key_path, 0o600)  # Restrict permissions
                logger.info(f"✓ Generated and saved new encryption key to {key_path}")
            except Exception as e:
                logger.warning(f"Could not save key to {key_path}: {e}")
        else:
            logger.warning("⚠ Using ephemeral encryption key (not persisted)")
        
        return key
    
    def encrypt_pii(self, original_text: str, associated_data: Optional[Dict] = None) -> Dict:
        """
        Encrypt PII text using AES-GCM.
        
        Args:
            original_text: Original text containing PII
            associated_data: Optional metadata to authenticate (not encrypted)
            
        Returns:
            Dictionary with vault entry data
        """
        if PII_STORAGE_MODE == "never_store_original":
            logger.info("PII storage disabled, not encrypting")
            return None
        
        try:
            # Generate random nonce (12 bytes recommended for AES-GCM)
            nonce = os.urandom(12)
            
            # Prepare associated data for authentication
            aad = json.dumps(associated_data or {}, sort_keys=True).encode('utf-8')
            
            # Encrypt
            ciphertext = self.aesgcm.encrypt(
                nonce,
                original_text.encode('utf-8'),
                aad
            )
            
            # Create vault entry
            vault_entry = {
                "_id": ObjectId(),
                "vault_ciphertext": base64.b64encode(ciphertext).decode('utf-8'),
                "nonce": base64.b64encode(nonce).decode('utf-8'),
                "key_version": self.key_version,
                "associated_data": associated_data,
                "created_at": datetime.utcnow(),
                "expires_at": datetime.utcnow() + timedelta(days=VAULT_TTL_DAYS)
            }
            
            logger.info(f"✓ Encrypted PII for vault entry {vault_entry['_id']}")
            return vault_entry
            
        except Exception as e:
            logger.error(f"✗ Encryption failed: {e}")
            raise
    
    def decrypt_pii(self, vault_entry: Dict) -> str:
        """
        Decrypt PII from vault entry.
        
        Args:
            vault_entry: Vault entry from MongoDB
            
        Returns:
            Decrypted original text
        """
        try:
            # Check key version
            if vault_entry.get("key_version") != self.key_version:
                raise ValueError(
                    f"Key version mismatch: vault has {vault_entry.get('key_version')}, "
                    f"current is {self.key_version}"
                )
            
            # Decode components
            ciphertext = base64.b64decode(vault_entry["vault_ciphertext"])
            nonce = base64.b64decode(vault_entry["nonce"])
            
            # Prepare associated data
            aad = json.dumps(
                vault_entry.get("associated_data", {}),
                sort_keys=True
            ).encode('utf-8')
            
            # Decrypt
            plaintext = self.aesgcm.decrypt(nonce, ciphertext, aad)
            
            logger.info(f"✓ Decrypted PII from vault entry {vault_entry['_id']}")
            return plaintext.decode('utf-8')
            
        except Exception as e:
            logger.error(f"✗ Decryption failed: {e}")
            raise
    
    def rotate_key(self, old_key_path: str, new_key_path: str):
        """
        Rotate encryption key (requires re-encryption of all vault entries).
        
        This should be done through a dedicated admin script, not at runtime.
        """
        raise NotImplementedError(
            "Key rotation must be performed through admin script with database access"
        )


# Singleton instance
_vault_instance = None

def get_pii_vault(key_path: Optional[str] = None) -> PIIVault:
    """
    Get or create singleton PII vault instance.
    
    Args:
        key_path: Path to encryption key file
        
    Returns:
        PIIVault instance
    """
    global _vault_instance
    if _vault_instance is None:
        # Default key path
        if key_path is None:
            key_path = os.path.join(
                os.path.dirname(__file__),
                "..",
                ".keys",
                "pii_vault.key"
            )
        _vault_instance = PIIVault(key_path)
    return _vault_instance


async def store_encrypted_pii(
    database,
    original_text: str,
    session_id: str,
    user_id: str
) -> Optional[str]:
    """
    Store encrypted PII in vault and return vault_id.
    
    Args:
        database: MongoDB database instance
        original_text: Original text to encrypt
        session_id: Session identifier
        user_id: User identifier
        
    Returns:
        Vault entry ObjectId as string, or None if storage disabled
    """
    if PII_STORAGE_MODE == "never_store_original":
        return None
    
    try:
        vault = get_pii_vault()
        
        # Create vault entry
        vault_entry = vault.encrypt_pii(
            original_text,
            associated_data={
                "session_id": session_id,
                "user_id": user_id,
                "purpose": "troubleshooting"
            }
        )
        
        # Store in MongoDB
        result = await database.pii_vault.insert_one(vault_entry)
        
        logger.info(f"✓ Stored encrypted PII in vault: {result.inserted_id}")
        return str(result.inserted_id)
        
    except Exception as e:
        logger.error(f"✗ Failed to store encrypted PII: {e}")
        # Don't fail the entire request if vault storage fails
        return None


async def retrieve_encrypted_pii(database, vault_id: str) -> Optional[str]:
    """
    Retrieve and decrypt PII from vault.
    
    Args:
        database: MongoDB database instance
        vault_id: Vault entry ObjectId
        
    Returns:
        Decrypted original text, or None if not found
    """
    try:
        vault_entry = await database.pii_vault.find_one({"_id": ObjectId(vault_id)})
        
        if not vault_entry:
            logger.warning(f"Vault entry {vault_id} not found")
            return None
        
        # Check if expired
        if vault_entry.get("expires_at") and vault_entry["expires_at"] < datetime.utcnow():
            logger.warning(f"Vault entry {vault_id} has expired")
            return None
        
        # Decrypt
        vault = get_pii_vault()
        original_text = vault.decrypt_pii(vault_entry)
        
        return original_text
        
    except Exception as e:
        logger.error(f"✗ Failed to retrieve encrypted PII: {e}")
        return None
