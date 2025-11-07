# PII Privacy & Anonymization Implementation Guide

## ✅ What Has Been Implemented

### 1. **PII Redaction Module** (`backend/privacy/pii_redactor.py`)

Comprehensive NER-based PII detection and redaction:

**Features:**
- ✅ spaCy NER for names, locations, organizations
- ✅ Regex patterns for emails, phones, SSN, credit cards, IDs, IP addresses
- ✅ Placeholder system (`[NAME_1]`, `[EMAIL_1]`, etc.)
- ✅ PII metadata generation (counts only, no original values)
- ✅ Validation to detect remaining PII

**Usage:**
```python
from privacy.pii_redactor import redact_pii

text = "John Doe (john@example.com) lives in NYC. Call 555-1234."
redacted_text, pii_metadata = redact_pii(text)

# redacted_text: "[NAME_1] ([EMAIL_1]) lives in [LOCATION_1]. Call [PHONE_1]."
# pii_metadata: {"names": 1, "emails": 1, "locations": 1, "phones": 1, ...}
```

### 2. **PII Encryption Vault** (`backend/privacy/pii_vault.py`)

AES-GCM authenticated encryption for optional encrypted storage:

**Features:**
- ✅ AES-256-GCM encryption with 12-byte nonce
- ✅ Key versioning support
- ✅ Authenticated encryption with associated data
- ✅ Automatic key generation and secure storage
- ✅ TTL-based expiration (7 days default)
- ✅ Mode control via `PII_STORAGE_MODE` environment variable

**Modes:**
- `never_store_original` (default): No original PII stored
- `store_encrypted_with_key`: Store encrypted in `pii_vault` collection

### 3. **Privacy Configuration** (`backend/privacy_config.json`)

Centralized privacy settings:
- PII redaction toggles
- Encryption settings
- Retention policies
- Consent enforcement rules
- Security limits

## 🔧 Integration Required

### Step 1: Update `api_endpoints.py` to Use PII Redaction

**Current flow:**
```
Audio → Whisper → original_text → Store directly
```

**New privacy-first flow:**
```
Audio → Whisper → original_text → redact_pii() → redacted_text → Store
                                              ↓
                             Optional: encrypt_pii() → pii_vault
```

**Implementation:**

```python
# In backend/api_endpoints.py

from privacy.pii_redactor import redact_pii
from privacy.pii_vault import store_encrypted_pii

@router.post("/upload/audio", response_model=AudioProcessResult, status_code=202)
async def upload_audio(...):
    # ... existing audio processing ...
    
    result = await audio_processor.process_audio(temp_path, language, timeout=300)
    original_text = result["original_text"]
    
    # === NEW: Redact PII ===
    redacted_text, pii_metadata = redact_pii(original_text)
    
    # Validate redaction
    if not PIIRedactor().validate_redaction(original_text, redacted_text):
        logger.error("PII redaction validation failed!")
        raise HTTPException(
            status_code=500,
            detail="Failed to properly redact PII. Session not stored for safety."
        )
    
    # === Store encrypted original if enabled ===
    pii_vault_id = None
    if PII_STORAGE_MODE == "store_encrypted_with_key":
        pii_vault_id = await store_encrypted_pii(
            database, original_text, session_id, session["user_id"]
        )
    
    # === Store with redacted text ===
    if session["allow_storage"]:
        text_processor = get_text_processor()
        text_result = await text_processor.process_text(
            redacted_text,  # ← Use redacted, not original
            compute_embedding=True,
            lowercase_tokens=False
        )
        
        answer_doc = {
            "session_id": session_id,
            "user_id": session["user_id"],
            "consent_id": session["consent_id"],
            "redacted_text": redacted_text,  # ← Store redacted
            "tokens": text_result["tokens"],
            "token_count": text_result["token_count"],
            "pii_metadata": pii_metadata,    # ← Store counts only
            "pii_vault_id": pii_vault_id,    # ← Reference to encrypted original
            "stt_confidence": result["stt_confidence"],
            "embedding": text_result.get("embedding"),
            "embedding_present": text_result["embedding_present"],
            "created_at": datetime.utcnow()
        }
        await database.answers.insert_one(answer_doc)
        logger.info(f"✓ Stored redacted transcript for session {session_id}")
    
    # Return redacted text to user (never return original with PII)
    return AudioProcessResult(
        session_id=session_id,
        original_text=redacted_text,  # ← Return redacted
        stt_confidence=result["stt_confidence"],
        ...
    )
```

### Step 2: Updated MongoDB Schema

**Old schema:**
```javascript
{
  "original_text": "John Doe called 555-1234",  // ❌ Contains PII
  "tokens": ["John", "Doe", "called", "555-1234"]
}
```

**New privacy-first schema:**
```javascript
{
  "_id": ObjectId("..."),
  "session_id": "session_abc",
  "user_id": "user_123",
  "consent_id": "consent_xyz",
  
  // Redacted text (PII replaced with placeholders)
  "redacted_text": "[NAME_1] called [PHONE_1]",
  
  // Tokens from redacted text
  "tokens": ["[NAME_1]", "called", "[PHONE_1]"],
  "token_count": 3,
  
  // PII metadata (counts only, no original values)
  "pii_metadata": {
    "names": 1,
    "emails": 0,
    "phones": 1,
    "locations": 0,
    "total_redactions": 2,
    "placeholders": {
      "[NAME_1]": "name",
      "[PHONE_1]": "phone"
    }
  },
  
  // Optional reference to encrypted original (if enabled)
  "pii_vault_id": "507f1f77bcf86cd799439011",  // or null
  
  // Analysis results
  "stt_confidence": 0.95,
  "embedding": [0.1, 0.2, ...],
  "embedding_present": true,
  
  "created_at": ISODate("2025-11-06T20:00:00Z")
}
```

**New `pii_vault` collection (only if encryption enabled):**
```javascript
{
  "_id": ObjectId("507f1f77bcf86cd799439011"),
  "vault_ciphertext": "base64_encrypted_data...",
  "nonce": "base64_nonce...",
  "key_version": "v1",
  "associated_data": {
    "session_id": "session_abc",
    "user_id": "user_123",
    "purpose": "troubleshooting"
  },
  "created_at": ISODate("2025-11-06T20:00:00Z"),
  "expires_at": ISODate("2025-11-13T20:00:00Z")  // 7 days TTL
}
```

### Step 3: Create Indexes

```javascript
// TTL index for automatic vault deletion
db.pii_vault.createIndex(
  { "expires_at": 1 },
  { expireAfterSeconds: 0 }
)

// Index for vault lookups
db.pii_vault.createIndex({ "_id": 1, "key_version": 1 })

// Index for audit queries
db.pii_vault.createIndex({ "associated_data.user_id": 1, "created_at": -1 })
```

## 🎯 Testing PII Redaction

### Test Cases

```python
# Test 1: Names
text = "John Doe and Jane Smith discussed the project"
redacted, meta = redact_pii(text)
assert "[NAME_1]" in redacted
assert "[NAME_2]" in redacted
assert meta["names"] == 2

# Test 2: Emails with obfuscation
text = "Contact john @ example . com or jane@test.com"
redacted, meta = redact_pii(text)
assert "[EMAIL_1]" in redacted
assert "[EMAIL_2]" in redacted
assert "john" not in redacted.lower()

# Test 3: Phone numbers (multiple formats)
test_cases = [
    "Call 555-123-4567",
    "Phone: (555) 123-4567",
    "Contact: 5551234567",
    "+1 555-123-4567"
]
for text in test_cases:
    redacted, meta = redact_pii(text)
    assert "[PHONE_" in redacted
    assert meta["phones"] > 0

# Test 4: SSN
text = "SSN: 123-45-6789"
redacted, meta = redact_pii(text)
assert "[SSN_1]" in redacted
assert "123-45-6789" not in redacted

# Test 5: Mixed PII
text = "John (john@example.com) at 123 Main St, called 555-1234 re: ID-1234567"
redacted, meta = redact_pii(text)
assert meta["total_redactions"] >= 4
```

## 🔐 Security Configuration

### Environment Variables

```bash
# .env file
PII_STORAGE_MODE=never_store_original  # or store_encrypted_with_key
VAULT_KEY_VERSION=v1
VAULT_TTL_DAYS=7
TEXT_RETENTION_DAYS=30
ANALYSIS_RETENTION_DAYS=90
```

### Key Management

**Option 1: Local Key File (Development)**
```bash
# Generate key
python -c "from cryptography.hazmat.primitives.ciphers.aead import AESGCM; import os; open('backend/.keys/pii_vault.key', 'wb').write(AESGCM.generate_key(256))"

# Set permissions
chmod 600 backend/.keys/pii_vault.key
```

**Option 2: AWS KMS (Production)**
```python
# Not yet implemented - requires AWS SDK integration
# TODO: Add KMS support in pii_vault.py
```

## 📊 Admin API for Vault Management

**Retrieve original PII (admin only):**
```python
from privacy.pii_vault import retrieve_encrypted_pii

@router.get("/admin/vault/{vault_id}", tags=["Admin"])
async def get_vault_entry(vault_id: str, database=Depends(get_database)):
    """Retrieve original PII from vault (requires admin auth)"""
    # TODO: Add admin authentication
    original_text = await retrieve_encrypted_pii(database, vault_id)
    return {"original_text": original_text}
```

## 🗑️ Retention & Deletion (TODO)

### What Needs to be Built

1. **Retention Scheduler** (`backend/retention_scheduler.py`)
   - Use APScheduler for background jobs
   - Run daily deletion sweep
   - Respect retention policies from config

2. **Soft Delete Implementation**
   - Add `deleted` flag to documents
   - Move to `deletion_audit` collection
   - Purge after delay period

3. **Admin APIs**
   - GET `/admin/retention/status`
   - POST `/admin/retention/run`
   - GET `/admin/retention/logs`

## 🎨 Frontend Changes Needed

### 1. Privacy Indicator

```jsx
// components/PrivacyIndicator.jsx
const PrivacyIndicator = ({ anonymizationEnabled }) => {
  return (
    <div className="privacy-notice">
      <span className="privacy-icon">🔒</span>
      {anonymizationEnabled ? (
        <p>Your data will be anonymized before storage</p>
      ) : (
        <p>Data stored with consent</p>
      )}
      <a href="/privacy-policy">Learn more</a>
    </div>
  );
};
```

### 2. Enhanced Consent Modal

```jsx
// Add to ConsentModal.js
<label>
  <input
    type="checkbox"
    name="anonymize_pii"
    checked={consent.anonymize_pii}
    onChange={handleChange}
  />
  Allow analysis but anonymize my personal information
  (names, emails, phone numbers will be redacted)
</label>
```

### 3. Delete Session Button

```jsx
const DeleteSessionButton = ({ sessionId }) => {
  const handleDelete = async () => {
    const confirmed = confirm(
      "Are you sure you want to delete this session? This cannot be undone."
    );
    if (confirmed) {
      await fetch(`/api/session/${sessionId}/delete_request`, {
        method: 'POST'
      });
      alert("Session deletion requested");
    }
  };
  
  return (
    <button onClick={handleDelete} className="delete-session-btn">
      🗑️ Delete My Session
    </button>
  );
};
```

## 📝 Requirements File Updates

Add to `requirements_evaluation.txt`:
```
cryptography>=41.0.0    # For AES-GCM encryption
spacy>=3.7.0            # For NER
APScheduler>=3.10.0     # For retention jobs
```

Install spaCy model:
```bash
python -m spacy download en_core_web_sm
```

## ✅ Implementation Checklist

### Phase 1: Core Privacy (Completed)
- [x] PII redaction module with NER
- [x] Encryption vault with AES-GCM
- [x] Privacy configuration file
- [x] Key management system

### Phase 2: Integration (In Progress)
- [ ] Update `/upload/audio` endpoint with PII redaction
- [ ] Update `/process/text` endpoint with PII redaction
- [ ] Update MongoDB schema
- [ ] Create TTL indexes
- [ ] Update evaluation service to handle redacted text

### Phase 3: Retention System (TODO)
- [ ] Build retention scheduler
- [ ] Implement soft delete
- [ ] Create admin retention APIs
- [ ] Add monitoring & alerts

### Phase 4: Frontend (TODO)
- [ ] Add privacy indicator
- [ ] Update consent modal
- [ ] Add delete session button
- [ ] Update AnswerDisplay to show redacted text

### Phase 5: Testing (TODO)
- [ ] Unit tests for PII redaction
- [ ] Integration tests for full pipeline
- [ ] Encryption/decryption tests
- [ ] Retention policy tests
- [ ] Adversarial PII test cases

### Phase 6: Documentation (TODO)
- [ ] Privacy policy updates
- [ ] User-facing privacy guide
- [ ] Admin operations manual
- [ ] Migration script for existing data

## 🚀 Quick Start

1. **Install dependencies:**
```bash
pip install cryptography spacy
python -m spacy download en_core_web_sm
```

2. **Test PII redaction:**
```python
from backend.privacy.pii_redactor import redact_pii

text = "John Doe (john@example.com) called 555-1234"
redacted, metadata = redact_pii(text)
print(f"Redacted: {redacted}")
print(f"Metadata: {metadata}")
```

3. **Configure privacy mode:**
```bash
export PII_STORAGE_MODE=never_store_original
```

4. **Integrate into endpoints** (see Step 1 above)

## ⚠️ Critical Security Notes

1. **Never log original PII** - Always log redacted text
2. **Restrict vault access** - Only privileged admin services
3. **Rotate keys regularly** - Every 90 days
4. **Monitor vault access** - Alert on unexpected access
5. **Test redaction thoroughly** - Use adversarial examples
6. **Fail safely** - If redaction fails, don't store session

## 📚 Additional Resources

- **spaCy NER docs**: https://spacy.io/usage/linguistic-features#named-entities
- **AES-GCM**: https://cryptography.io/en/latest/hazmat/primitives/aead/
- **GDPR compliance**: https://gdpr.eu/
- **PII best practices**: https://www.nist.gov/privacy-framework

---

**Status:** Core privacy modules implemented. Integration and testing phases pending.
