"""
Key Store Abstraction for Encryption Key Management
Supports KMS (AWS KMS, GCP KMS, HashiCorp Vault) and local file mode
"""

import os
import json
import base64
import logging
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

# Environment configuration
KEY_STORE_MODE = os.getenv('KEY_STORE_MODE', 'local')  # 'kms' or 'local'
KEY_STORE_PATH = os.getenv('KEY_STORE_PATH', os.path.join(os.path.dirname(__file__), '..', 'keys'))
KMS_PROVIDER = os.getenv('KMS_PROVIDER', 'aws')  # 'aws', 'gcp', 'vault'
KMS_KEY_ID = os.getenv('KMS_KEY_ID', '')
KEY_VERSION = os.getenv('KEY_VERSION', 'v1')
KEY_ROTATION_DAYS = int(os.getenv('KEY_ROTATION_DAYS', '90'))


class KeyStore(ABC):
    """Abstract base class for key storage"""
    
    @abstractmethod
    def get_data_key(self, key_version: str) -> bytes:
        """Get plaintext data encryption key for given version"""
        pass
    
    @abstractmethod
    def wrap_data_key(self, plaintext_key: bytes, key_version: str) -> str:
        """Wrap (encrypt) data key with master key, return base64 wrapped key"""
        pass
    
    @abstractmethod
    def unwrap_data_key(self, wrapped_key: str, key_version: str) -> bytes:
        """Unwrap (decrypt) data key using master key"""
        pass
    
    @abstractmethod
    def rotate_key(self) -> str:
        """Generate new key version and return version ID"""
        pass
    
    @abstractmethod
    def get_current_version(self) -> str:
        """Get current active key version"""
        pass


class LocalKeyStore(KeyStore):
    """Local file-based key store (DEV/TEST ONLY - NOT FOR PRODUCTION)"""
    
    def __init__(self, key_dir: str):
        self.key_dir = key_dir
        os.makedirs(key_dir, exist_ok=True)
        
        # Set restrictive permissions (Unix/Linux only)
        try:
            os.chmod(key_dir, 0o700)
        except:
            pass
        
        self.metadata_file = os.path.join(key_dir, 'key_metadata.json')
        self._ensure_metadata()
        
        logger.warning("🔓 Using LOCAL key store - FOR DEVELOPMENT ONLY!")
    
    def _ensure_metadata(self):
        """Ensure metadata file exists"""
        if not os.path.exists(self.metadata_file):
            metadata = {
                "current_version": KEY_VERSION,
                "keys": {},
                "created_at": datetime.utcnow().isoformat(),
                "rotation_days": KEY_ROTATION_DAYS
            }
            self._save_metadata(metadata)
    
    def _load_metadata(self) -> Dict:
        """Load metadata from file"""
        with open(self.metadata_file, 'r') as f:
            return json.load(f)
    
    def _save_metadata(self, metadata: Dict):
        """Save metadata to file"""
        with open(self.metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Set restrictive permissions
        try:
            os.chmod(self.metadata_file, 0o600)
        except:
            pass
    
    def _get_key_path(self, key_version: str) -> str:
        """Get file path for key version"""
        return os.path.join(self.key_dir, f'key_{key_version}.bin')
    
    def get_data_key(self, key_version: str) -> bytes:
        """Get plaintext data encryption key"""
        key_path = self._get_key_path(key_version)
        
        if not os.path.exists(key_path):
            # Generate new key
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
            data_key = AESGCM.generate_key(bit_length=256)
            
            with open(key_path, 'wb') as f:
                f.write(data_key)
            
            # Set restrictive permissions
            try:
                os.chmod(key_path, 0o600)
            except:
                pass
            
            # Update metadata
            metadata = self._load_metadata()
            metadata['keys'][key_version] = {
                "created_at": datetime.utcnow().isoformat(),
                "algorithm": "AES-256-GCM",
                "status": "active"
            }
            self._save_metadata(metadata)
            
            logger.info(f"Generated new data key for version {key_version}")
        
        with open(key_path, 'rb') as f:
            return f.read()
    
    def wrap_data_key(self, plaintext_key: bytes, key_version: str) -> str:
        """In local mode, just base64 encode (no real wrapping)"""
        # In real KMS mode, this would encrypt with master key
        return base64.b64encode(plaintext_key).decode('utf-8')
    
    def unwrap_data_key(self, wrapped_key: str, key_version: str) -> bytes:
        """In local mode, just base64 decode"""
        return base64.b64decode(wrapped_key)
    
    def rotate_key(self) -> str:
        """Generate new key version"""
        metadata = self._load_metadata()
        
        # Generate new version ID
        current_num = int(metadata['current_version'].replace('v', ''))
        new_version = f'v{current_num + 1}'
        
        # Mark old key as deprecated
        old_version = metadata['current_version']
        if old_version in metadata['keys']:
            metadata['keys'][old_version]['status'] = 'deprecated'
            metadata['keys'][old_version]['deprecated_at'] = datetime.utcnow().isoformat()
        
        # Update current version
        metadata['current_version'] = new_version
        metadata['last_rotation'] = datetime.utcnow().isoformat()
        self._save_metadata(metadata)
        
        # Generate new key (will be created on first access)
        logger.info(f"Key rotated: {old_version} -> {new_version}")
        
        return new_version
    
    def get_current_version(self) -> str:
        """Get current active key version"""
        metadata = self._load_metadata()
        return metadata['current_version']


class AWSKMSKeyStore(KeyStore):
    """AWS KMS-based key store (PRODUCTION)"""
    
    def __init__(self, kms_key_id: str, region: str = None):
        self.kms_key_id = kms_key_id
        self.region = region or os.getenv('AWS_REGION', 'us-east-1')
        
        try:
            import boto3
            self.kms_client = boto3.client('kms', region_name=self.region)
            logger.info(f"🔐 AWS KMS initialized: {kms_key_id}")
        except ImportError:
            raise RuntimeError("boto3 required for AWS KMS. Install: pip install boto3")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize AWS KMS: {e}")
    
    def get_data_key(self, key_version: str) -> bytes:
        """Generate data encryption key using KMS"""
        try:
            response = self.kms_client.generate_data_key(
                KeyId=self.kms_key_id,
                KeySpec='AES_256'
            )
            return response['Plaintext']
        except Exception as e:
            logger.error(f"KMS generate_data_key failed: {e}")
            raise
    
    def wrap_data_key(self, plaintext_key: bytes, key_version: str) -> str:
        """Encrypt data key with KMS master key"""
        try:
            response = self.kms_client.encrypt(
                KeyId=self.kms_key_id,
                Plaintext=plaintext_key
            )
            return base64.b64encode(response['CiphertextBlob']).decode('utf-8')
        except Exception as e:
            logger.error(f"KMS encrypt failed: {e}")
            raise
    
    def unwrap_data_key(self, wrapped_key: str, key_version: str) -> bytes:
        """Decrypt data key using KMS"""
        try:
            ciphertext_blob = base64.b64decode(wrapped_key)
            response = self.kms_client.decrypt(
                CiphertextBlob=ciphertext_blob
            )
            return response['Plaintext']
        except Exception as e:
            logger.error(f"KMS decrypt failed: {e}")
            raise
    
    def rotate_key(self) -> str:
        """Rotate KMS key"""
        try:
            # AWS KMS handles automatic rotation
            # We just increment our version tracking
            new_version = f"v{int(datetime.utcnow().timestamp())}"
            logger.info(f"KMS key rotation scheduled, new version: {new_version}")
            return new_version
        except Exception as e:
            logger.error(f"KMS rotation failed: {e}")
            raise
    
    def get_current_version(self) -> str:
        """Get current key version"""
        return KEY_VERSION


class GCPKMSKeyStore(KeyStore):
    """GCP KMS-based key store (PRODUCTION)"""
    
    def __init__(self, key_name: str):
        self.key_name = key_name
        
        try:
            from google.cloud import kms
            self.kms_client = kms.KeyManagementServiceClient()
            logger.info(f"🔐 GCP KMS initialized: {key_name}")
        except ImportError:
            raise RuntimeError("google-cloud-kms required. Install: pip install google-cloud-kms")
    
    def get_data_key(self, key_version: str) -> bytes:
        """Generate data key (GCP doesn't have direct data key generation)"""
        import secrets
        return secrets.token_bytes(32)  # AES-256 key
    
    def wrap_data_key(self, plaintext_key: bytes, key_version: str) -> str:
        """Encrypt with GCP KMS"""
        try:
            response = self.kms_client.encrypt(
                request={"name": self.key_name, "plaintext": plaintext_key}
            )
            return base64.b64encode(response.ciphertext).decode('utf-8')
        except Exception as e:
            logger.error(f"GCP KMS encrypt failed: {e}")
            raise
    
    def unwrap_data_key(self, wrapped_key: str, key_version: str) -> bytes:
        """Decrypt with GCP KMS"""
        try:
            ciphertext = base64.b64decode(wrapped_key)
            response = self.kms_client.decrypt(
                request={"name": self.key_name, "ciphertext": ciphertext}
            )
            return response.plaintext
        except Exception as e:
            logger.error(f"GCP KMS decrypt failed: {e}")
            raise
    
    def rotate_key(self) -> str:
        """Rotate GCP KMS key"""
        new_version = f"v{int(datetime.utcnow().timestamp())}"
        logger.info(f"GCP KMS key rotation, new version: {new_version}")
        return new_version
    
    def get_current_version(self) -> str:
        return KEY_VERSION


def get_key_store() -> KeyStore:
    """Factory function to get appropriate key store"""
    
    if KEY_STORE_MODE == 'kms':
        if KMS_PROVIDER == 'aws':
            if not KMS_KEY_ID:
                raise ValueError("KMS_KEY_ID environment variable required for AWS KMS")
            return AWSKMSKeyStore(KMS_KEY_ID)
        
        elif KMS_PROVIDER == 'gcp':
            if not KMS_KEY_ID:
                raise ValueError("KMS_KEY_ID environment variable required for GCP KMS")
            return GCPKMSKeyStore(KMS_KEY_ID)
        
        else:
            raise ValueError(f"Unsupported KMS provider: {KMS_PROVIDER}")
    
    elif KEY_STORE_MODE == 'local':
        return LocalKeyStore(KEY_STORE_PATH)
    
    else:
        raise ValueError(f"Invalid KEY_STORE_MODE: {KEY_STORE_MODE}")


# Global key store instance
_key_store: Optional[KeyStore] = None

def init_key_store() -> KeyStore:
    """Initialize global key store"""
    global _key_store
    if _key_store is None:
        _key_store = get_key_store()
    return _key_store

def get_current_key_store() -> KeyStore:
    """Get initialized key store"""
    if _key_store is None:
        return init_key_store()
    return _key_store
