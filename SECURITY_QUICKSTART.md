# Security System Quick Start

## 🚀 5-Minute Integration Guide

### Step 1: Install Dependencies

```bash
cd backend
pip install cryptography PyJWT
```

### Step 2: Create `__init__.py` in security folder

```python
# backend/security/__init__.py
from .key_store import init_key_store, get_current_key_store
from .field_encryption import encrypt_field, decrypt_field, encrypt_document_fields, decrypt_document_fields
from .rbac import require_auth, require_permission, Role, generate_jwt_token, create_dev_admin_token
from .audit_logger import init_audit_logger, get_audit_logger

__all__ = [
    'init_key_store',
    'get_current_key_store',
    'encrypt_field',
    'decrypt_field',
    'encrypt_document_fields',
    'decrypt_document_fields',
    'require_auth',
    'require_permission',
    'Role',
    'generate_jwt_token',
    'create_dev_admin_token',
    'init_audit_logger',
    'get_audit_logger'
]
```

### Step 3: Initialize in `app.py`

Add after MongoDB connection:

```python
# backend/app.py (add after MongoDB connection)

# Import security system
from security import init_key_store, init_audit_logger, create_dev_admin_token

# Initialize security
try:
    key_store = init_key_store()
    audit_logger = init_audit_logger(db)
    
    # Generate dev admin token for testing
    dev_token = create_dev_admin_token()
    logger.info(f"🔐 Security system initialized")
    logger.info(f"🔓 DEV Admin Token: {dev_token}")
    logger.info(f"   Use this token in Authorization: Bearer {dev_token}")
except Exception as e:
    logger.error(f"Failed to initialize security: {e}")
```

### Step 4: Test with Curl

```bash
# Get admin token from logs
TOKEN="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."

# Test protected endpoint
curl -H "Authorization: Bearer $TOKEN" \
     http://localhost:5001/api/interviews/123

# Test decrypt with justification
curl -X POST \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"reason": "Investigating user complaint ticket #456 - approved by supervisor", "fields": ["transcribed_text"]}' \
     http://localhost:5001/api/interviews/123/decrypt
```

### Step 5: Encrypt Data Before Saving

```python
# Example: Encrypting interview response before storage

from security import encrypt_document_fields, get_audit_logger

# Your existing data
interview_data = {
    "user_id": "user@example.com",
    "session_id": "session_123",
    "transcribed_text": "I have experience with Python...",
    "tokens": ["I", "have", "experience", "with", "Python"],
    "embedding": [0.1, 0.2, 0.3, ...],
    "anonymized_answer": "I have experience with [ORG]",
    "score": 0.85,
    "feedback": "Good answer"
}

# Encrypt sensitive fields
encrypted_doc = encrypt_document_fields(
    interview_data,
    fields_to_encrypt=["transcribed_text", "tokens", "embedding"],
    associated_data={"user_id": interview_data["user_id"]}
)

# Store in MongoDB
result = interviews.insert_one(encrypted_doc)

# Log the write
audit_logger = get_audit_logger()
audit_logger.log_write(
    target_collection="interviews",
    target_id=str(result.inserted_id),
    fields_modified=["transcribed_text", "tokens", "embedding"]
)
```

### Step 6: Protect Endpoint with RBAC

```python
from security import require_auth, Role, get_current_user, filter_response_by_role

@app.route('/api/interviews/<interview_id>', methods=['GET'])
@require_auth(required_roles=[Role.ANALYST, Role.ADMIN])
def get_interview(interview_id):
    """Get interview with role-based filtering"""
    
    # Get current user from token
    user = get_current_user()
    
    # Fetch from database
    interview = interviews.find_one({"id": interview_id})
    
    if not interview:
        return jsonify({"error": "Not found"}), 404
    
    # Log access
    audit_logger = get_audit_logger()
    audit_logger.log_read(
        target_collection="interviews",
        target_id=interview_id,
        fields_accessed=list(interview.keys())
    )
    
    # Filter based on role (readers see less, admins see all)
    filtered = filter_response_by_role(interview, user['roles'])
    
    return jsonify(filtered), 200
```

---

## 🎯 What You Get

### ✅ Field-Level Encryption
- **AES-256-GCM** authenticated encryption
- **Automatic key rotation** support
- **KMS integration** (AWS/GCP) for production
- **Tamper-evident** metadata

### ✅ RBAC
- **4 roles**: reader, analyst, admin, system
- **JWT tokens** with automatic expiration
- **Hierarchical permissions** (admin inherits analyst)
- **Field-level filtering** based on role

### ✅ Audit Logging
- **Write-only** immutable logs
- **Hash chain** for tamper detection
- **Automatic actor tracking** from Flask context
- **Required justification** for decrypt
- **IP and User-Agent** logging

---

## 📊 MongoDB Schema

### Before (Insecure):
```javascript
{
  "transcribed_text": "My name is John Smith...",  // ❌ Plaintext PII
  "tokens": ["My", "name", "is", "John", "Smith"],
  "embedding": [0.1, 0.2, 0.3]
}
```

### After (Secure):
```javascript
{
  "_encrypted_transcribed_text": {
    "ciphertext": "ZXhhbXBsZQ==",  // ✅ Encrypted
    "nonce": "...",
    "key_version": "v1",
    "algorithm": "AES-256-GCM"
  },
  "_encryption_metadata": {
    "encrypted": true,
    "encrypted_fields": ["transcribed_text", "tokens", "embedding"]
  },
  "anonymized_answer": "My name is [NAME]...",  // ✅ Safe to show
  "score": 0.85
}
```

---

## 🔐 Token Examples

### Generate Tokens for Different Roles:

```python
from security import generate_jwt_token, Role

# Admin token
admin_token = generate_jwt_token("admin@example.com", [Role.ADMIN])

# Analyst token
analyst_token = generate_jwt_token("analyst@example.com", [Role.ANALYST])

# Reader token
reader_token = generate_jwt_token("reader@example.com", [Role.READER])

# System/service token
service_token = generate_jwt_token("service:background-job", [Role.SYSTEM])

print(f"Admin: {admin_token}")
```

### Use Token in Request:

```python
import requests

response = requests.get(
    'http://localhost:5001/api/interviews/123',
    headers={'Authorization': f'Bearer {admin_token}'}
)
```

---

## ⚠️ Common Issues

### Issue 1: "No authentication token provided"
**Solution:** Add `Authorization: Bearer YOUR_TOKEN` header

### Issue 2: "Insufficient permissions"
**Solution:** Use correct role token (admin for decrypt, analyst for analysis)

### Issue 3: "Decryption requires detailed justification"
**Solution:** Provide reason with at least 20 characters

### Issue 4: "Key store not initialized"
**Solution:** Call `init_key_store()` before using encryption

---

## 🧪 Quick Test

```python
# test_security.py
from security import encrypt_field, decrypt_field, init_key_store

# Initialize
init_key_store()

# Test encryption
plaintext = "sensitive data"
encrypted = encrypt_field(plaintext)
decrypted = decrypt_field(encrypted)

assert plaintext == decrypted
print("✅ Encryption working!")

# Test tampering detection
encrypted['ciphertext'] = encrypted['ciphertext'][:-4] + "XXXX"
try:
    decrypt_field(encrypted)
    print("❌ Tampering detection failed!")
except:
    print("✅ Tampering detected!")
```

Run:
```bash
python test_security.py
```

---

## 📝 Environment Variables

```bash
# Development (Local Keys)
export KEY_STORE_MODE=local
export JWT_SECRET=dev-secret-change-in-production

# Production (AWS KMS)
export KEY_STORE_MODE=kms
export KMS_PROVIDER=aws
export KMS_KEY_ID=arn:aws:kms:us-east-1:123456789:key/abc-123
export JWT_SECRET=your-production-secret-minimum-32-characters
```

---

## ✅ Done!

You now have:
- ✅ Encrypted sensitive fields at rest
- ✅ Role-based access control
- ✅ Immutable audit logs
- ✅ JWT authentication
- ✅ Production-ready security

**Start the server and test with the admin token from logs!** 🚀

For complete documentation, see `SECURITY_IMPLEMENTATION_GUIDE.md`
