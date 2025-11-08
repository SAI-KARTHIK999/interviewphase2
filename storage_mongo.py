import os
import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from pymongo import MongoClient, ASCENDING
from pymongo.collection import Collection
from cryptography.fernet import Fernet


_client: Optional[MongoClient] = None
_collection: Optional[Collection] = None


def _get_fernet() -> Optional[Fernet]:
    key = os.getenv("PII_FERNET_KEY")
    if not key:
        return None
    try:
        return Fernet(key)
    except Exception:
        return None


def get_collection() -> Collection:
    global _client, _collection
    if _collection is not None:
        return _collection

    uri = os.getenv("MONGODB_URI")
    db_name = os.getenv("MONGODB_DB", "ai_app")
    coll_name = os.getenv("MONGODB_COLLECTION", "transcripts")

    if not uri:
        raise RuntimeError("MONGODB_URI is not set")

    _client = MongoClient(uri, retryWrites=True)
    db = _client[db_name]
    _collection = db[coll_name]

    # Indexes: user_id + created_at, TTL optional via env
    _collection.create_index([("user_id", ASCENDING), ("created_at", ASCENDING)])

    ttl_days = os.getenv("MONGODB_TTL_DAYS")
    if ttl_days:
        # Create TTL index on created_at
        try:
            seconds = int(float(ttl_days) * 86400)
            _collection.create_index("created_at", expireAfterSeconds=seconds)
        except Exception:
            pass

    return _collection


def store_transcript(
    *,
    user_id: str,
    raw_text: str,
    tokenized_text: str,
    meta: Dict[str, Any],
    timestamp: Optional[datetime] = None,
) -> str:
    """
    Store both raw and tokenized text with metadata.
    - raw_text is encrypted at rest if PII_FERNET_KEY is configured.
    - tokenized_text should already be anonymized/masked/redacted.
    """
    col = get_collection()

    created_at = datetime.now(timezone.utc)
    input_ts = timestamp.astimezone(timezone.utc) if timestamp else created_at

    f = _get_fernet()
    doc: Dict[str, Any] = {
        "user_id": user_id,
        "tokenized_text": tokenized_text,
        "meta": {
            **meta,
            "stored_with_encryption": bool(f is not None),
        },
        "created_at": created_at,
        "input_timestamp": input_ts,
    }

    if f is not None:
        doc["raw_text_encrypted"] = f.encrypt(raw_text.encode("utf-8"))
    else:
        # fallback: store plaintext, but mark in meta
        doc["raw_text"] = raw_text

    res = col.insert_one(doc)
    return str(res.inserted_id)
