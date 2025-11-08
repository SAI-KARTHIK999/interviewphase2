import os
import json
from datetime import datetime
from typing import Optional

from pii_sanitizer_enhanced import EnhancedPIISanitizer
from storage_mongo import store_transcript


_sanitizer: Optional[EnhancedPIISanitizer] = None

def get_sanitizer() -> EnhancedPIISanitizer:
    global _sanitizer
    if _sanitizer is None:
        mode = os.getenv("PII_MODE", "mask")  # mask|redact|hash|encrypt
        hipaa = os.getenv("PII_HIPAA_MODE", "true").lower() in {"1", "true", "yes"}
        _sanitizer = EnhancedPIISanitizer(mode=mode, hipaa_mode=hipaa)
    return _sanitizer


def process_and_store_transcript(*, user_id: str, transcript_text: str, timestamp: Optional[datetime] = None) -> str:
    """
    Entry-point for the transcription workflow:
      - Improves NER for names via custom recognizer + ASR normalization
      - Masks/removes emails, phones, locations (Presidio built-ins)
      - Stores raw_text and tokenized_text in MongoDB with metadata
    Returns inserted document id as string.
    """
    sanitizer = get_sanitizer()
    res = sanitizer.sanitize_text(transcript_text)

    meta = {
        "entity_counts": res.entity_counts,
        "sanitizer_mode": res.mode,
        "hipaa_mode": res.hipaa_mode,
        # store minimal details to aid QA without raw content
        "normalized": True,
    }

    doc_id = store_transcript(
        user_id=user_id,
        raw_text=transcript_text,
        tokenized_text=res.anonymized_text,
        meta=meta,
        timestamp=timestamp,
    )
    return doc_id


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Process and store a transcript")
    parser.add_argument("--user-id", required=True)
    parser.add_argument("--timestamp", default=None, help="ISO8601 timestamp")
    args = parser.parse_args()

    text = sys.stdin.read()
    ts = None
    if args.timestamp:
        try:
            ts = datetime.fromisoformat(args.timestamp)
        except Exception:
            ts = None

    doc_id = process_and_store_transcript(user_id=args.user_id, transcript_text=text, timestamp=ts)
    print(json.dumps({"inserted_id": doc_id}))
