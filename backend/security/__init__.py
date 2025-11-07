"""
Security Package for AI Interview Bot
Provides encryption, RBAC, and audit logging
"""

from .key_store import (
    init_key_store,
    get_current_key_store,
    KeyStore,
    LocalKeyStore,
    AWSKMSKeyStore,
    GCPKMSKeyStore
)

from .field_encryption import (
    encrypt_field,
    decrypt_field,
    encrypt_document_fields,
    decrypt_document_fields,
    verify_encryption_integrity,
    get_encryption_metadata,
    is_field_encrypted
)

from .rbac import (
    Role,
    require_auth,
    require_permission,
    get_current_user,
    generate_jwt_token,
    verify_jwt_token,
    check_permission,
    filter_response_by_role,
    create_service_token,
    create_dev_admin_token,
    create_dev_analyst_token,
    create_dev_reader_token
)

from .audit_logger import (
    AuditLogger,
    init_audit_logger,
    get_audit_logger,
    audit_log
)

__version__ = '1.0.0'

__all__ = [
    # Key Store
    'init_key_store',
    'get_current_key_store',
    'KeyStore',
    'LocalKeyStore',
    'AWSKMSKeyStore',
    'GCPKMSKeyStore',
    
    # Encryption
    'encrypt_field',
    'decrypt_field',
    'encrypt_document_fields',
    'decrypt_document_fields',
    'verify_encryption_integrity',
    'get_encryption_metadata',
    'is_field_encrypted',
    
    # RBAC
    'Role',
    'require_auth',
    'require_permission',
    'get_current_user',
    'generate_jwt_token',
    'verify_jwt_token',
    'check_permission',
    'filter_response_by_role',
    'create_service_token',
    'create_dev_admin_token',
    'create_dev_analyst_token',
    'create_dev_reader_token',
    
    # Audit Logging
    'AuditLogger',
    'init_audit_logger',
    'get_audit_logger',
    'audit_log'
]
