"""
Field-Level Encryption using AES-256-GCM
Provides encrypt_field() and decrypt_field() with authenticated encryption
"""

import os
import base64
import json
import logging
from typing import Any, Dict, Optional, Tuple
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from datetime import datetime

from .key_store import get_current_key_store, KEY_VERSION

logger = logging.getLogger(__name__)


def encrypt_field(
    plaintext: Any,
    key_version: Optional[str] = None,
    associated_data: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Encrypt a field using AES-256-GCM
    
    Args:
        plaintext: Data to encrypt (will be JSON serialized if not str/bytes)
        key_version: Key version to use (defaults to current)
        associated_data: Additional authenticated data (not encrypted but verified)
    
    Returns:
        Dict with ciphertext, nonce, key_version, and metadata
    """
    try:
        # Get key store and version
        key_store = get_current_key_store()
        if key_version is None:
            key_version = key_store.get_current_version()
        
        # Get encryption key
        data_key = key_store.get_data_key(key_version)
        
        # Prepare plaintext
        if isinstance(plaintext, bytes):
            plaintext_bytes = plaintext
        elif isinstance(plaintext, str):
            plaintext_bytes = plaintext.encode('utf-8')
        else:
            # JSON serialize for complex types
            plaintext_bytes = json.dumps(plaintext).encode('utf-8')
        
        # Prepare associated data for authentication
        aad_dict = {
            "timestamp": datetime.utcnow().isoformat(),
            "key_version": key_version,
            **(associated_data or {})
        }
        aad_bytes = json.dumps(aad_dict, sort_keys=True).encode('utf-8')
        
        # Encrypt with AES-GCM
        aesgcm = AESGCM(data_key)
        nonce = os.urandom(12)  # 96-bit nonce for GCM
        ciphertext = aesgcm.encrypt(nonce, plaintext_bytes, aad_bytes)
        
        # Return encrypted data package
        return {
            "ciphertext": base64.b64encode(ciphertext).decode('utf-8'),
            "nonce": base64.b64encode(nonce).decode('utf-8'),
            "key_version": key_version,
            "algorithm": "AES-256-GCM",
            "associated_data": aad_dict,
            "encrypted_at": datetime.utcnow()
        }
    
    except Exception as e:
        logger.error(f"Encryption failed: {e}")
        raise RuntimeError(f"Field encryption failed: {e}")


def decrypt_field(
    encrypted_data: Dict[str, Any],
    expected_key_version: Optional[str] = None
) -> Any:
    """
    Decrypt a field encrypted with encrypt_field()
    
    Args:
        encrypted_data: Dict returned by encrypt_field()
        expected_key_version: Optional version check for security
    
    Returns:
        Decrypted plaintext (str, bytes, or deserialized JSON)
    """
    try:
        # Extract components
        ciphertext = base64.b64decode(encrypted_data['ciphertext'])
        nonce = base64.b64decode(encrypted_data['nonce'])
        key_version = encrypted_data['key_version']
        associated_data = encrypted_data.get('associated_data', {})
        
        # Verify key version if specified
        if expected_key_version and key_version != expected_key_version:
            raise ValueError(f"Key version mismatch: expected {expected_key_version}, got {key_version}")
        
        # Get decryption key
        key_store = get_current_key_store()
        data_key = key_store.get_data_key(key_version)
        
        # Reconstruct associated data for authentication
        aad_bytes = json.dumps(associated_data, sort_keys=True).encode('utf-8')
        
        # Decrypt with AES-GCM (also verifies authentication tag)
        aesgcm = AESGCM(data_key)
        plaintext_bytes = aesgcm.decrypt(nonce, ciphertext, aad_bytes)
        
        # Try to decode as UTF-8 string
        try:
            plaintext_str = plaintext_bytes.decode('utf-8')
            
            # Try to parse as JSON
            try:
                return json.loads(plaintext_str)
            except json.JSONDecodeError:
                return plaintext_str
        
        except UnicodeDecodeError:
            # Return as bytes if not valid UTF-8
            return plaintext_bytes
    
    except Exception as e:
        logger.error(f"Decryption failed: {e}")
        raise RuntimeError(f"Field decryption failed: {e}")


def encrypt_document_fields(
    document: Dict[str, Any],
    fields_to_encrypt: list,
    associated_data: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Encrypt specified fields in a document
    
    Args:
        document: Document with fields to encrypt
        fields_to_encrypt: List of field names to encrypt
        associated_data: Additional context for encryption
    
    Returns:
        Modified document with encrypted fields and metadata
    """
    encrypted_doc = document.copy()
    encryption_metadata = {}
    
    for field_name in fields_to_encrypt:
        if field_name in document and document[field_name] is not None:
            # Add field name to associated data
            field_aad = {
                "field_name": field_name,
                **(associated_data or {})
            }
            
            # Encrypt field
            encrypted = encrypt_field(document[field_name], associated_data=field_aad)
            
            # Store in special field name
            encrypted_field_name = f"_encrypted_{field_name}"
            encrypted_doc[encrypted_field_name] = encrypted
            
            # Remove plaintext
            del encrypted_doc[field_name]
            
            # Track metadata
            encryption_metadata[field_name] = {
                "encrypted": True,
                "key_version": encrypted["key_version"],
                "encrypted_at": encrypted["encrypted_at"]
            }
    
    # Add encryption metadata to document
    encrypted_doc["_encryption_metadata"] = {
        "encrypted_fields": list(encryption_metadata.keys()),
        "field_metadata": encryption_metadata,
        "encrypted": True,
        "key_version": get_current_key_store().get_current_version()
    }
    
    return encrypted_doc


def decrypt_document_fields(
    encrypted_document: Dict[str, Any],
    fields_to_decrypt: Optional[list] = None
) -> Dict[str, Any]:
    """
    Decrypt specified fields in an encrypted document
    
    Args:
        encrypted_document: Document with encrypted fields
        fields_to_decrypt: List of fields to decrypt (None = all encrypted fields)
    
    Returns:
        Document with decrypted fields
    """
    if "_encryption_metadata" not in encrypted_document:
        # Document not encrypted
        return encrypted_document
    
    decrypted_doc = encrypted_document.copy()
    metadata = encrypted_document["_encryption_metadata"]
    encrypted_fields = metadata.get("encrypted_fields", [])
    
    # Determine which fields to decrypt
    if fields_to_decrypt is None:
        fields_to_decrypt = encrypted_fields
    
    for field_name in fields_to_decrypt:
        if field_name in encrypted_fields:
            encrypted_field_name = f"_encrypted_{field_name}"
            
            if encrypted_field_name in encrypted_document:
                # Decrypt field
                decrypted_value = decrypt_field(encrypted_document[encrypted_field_name])
                
                # Restore to original field name
                decrypted_doc[field_name] = decrypted_value
                
                # Remove encrypted version
                del decrypted_doc[encrypted_field_name]
    
    return decrypted_doc


def verify_encryption_integrity(encrypted_data: Dict[str, Any]) -> bool:
    """
    Verify encryption integrity without decrypting
    
    Args:
        encrypted_data: Encrypted field data
    
    Returns:
        True if integrity check passes
    """
    required_keys = {"ciphertext", "nonce", "key_version", "algorithm"}
    
    if not all(key in encrypted_data for key in required_keys):
        logger.warning("Missing required encryption keys")
        return False
    
    if encrypted_data.get("algorithm") != "AES-256-GCM":
        logger.warning(f"Unexpected algorithm: {encrypted_data.get('algorithm')}")
        return False
    
    return True


def get_encryption_metadata(encrypted_document: Dict[str, Any]) -> Optional[Dict]:
    """
    Extract encryption metadata from document
    
    Returns:
        Encryption metadata or None if not encrypted
    """
    return encrypted_document.get("_encryption_metadata")


def is_field_encrypted(document: Dict[str, Any], field_name: str) -> bool:
    """Check if a specific field is encrypted"""
    metadata = get_encryption_metadata(document)
    if metadata is None:
        return False
    return field_name in metadata.get("encrypted_fields", [])
