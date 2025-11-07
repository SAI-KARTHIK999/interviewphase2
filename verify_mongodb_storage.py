"""
Verification script to check what's actually stored in MongoDB
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

async def check_mongodb_storage():
    """Check what's stored in MongoDB answers collection"""
    
    # Connect to MongoDB
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["interview_db"]
    
    print("=" * 70)
    print("MONGODB STORAGE VERIFICATION")
    print("=" * 70)
    
    # Count total documents
    total_count = await db.answers.count_documents({})
    print(f"\n📊 Total answers in database: {total_count}")
    
    if total_count == 0:
        print("\n⚠️  No answers found in database!")
        print("   Make sure you've uploaded audio and allowed storage.")
        return
    
    # Get latest document
    latest = await db.answers.find_one(sort=[("created_at", -1)])
    
    if not latest:
        print("\n⚠️  Could not retrieve latest answer")
        return
    
    print(f"\n📄 Latest Answer Document:")
    print("-" * 70)
    print(f"Session ID: {latest.get('session_id', 'N/A')}")
    print(f"User ID: {latest.get('user_id', 'N/A')}")
    print(f"Created: {latest.get('created_at', 'N/A')}")
    print()
    
    # Check original_text
    if 'original_text' in latest:
        original = latest['original_text']
        print(f"✅ original_text: PRESENT ({len(original)} chars)")
        print(f"   Preview: {original[:100]}...")
    else:
        print(f"❌ original_text: MISSING")
    
    print()
    
    # Check redacted_text
    if 'redacted_text' in latest:
        redacted = latest['redacted_text']
        print(f"✅ redacted_text: PRESENT ({len(redacted)} chars)")
        print(f"   Preview: {redacted[:100]}...")
    else:
        print(f"ℹ️  redacted_text: Not present (using original_text)")
    
    print()
    
    # Check cleaned_text
    if 'cleaned_text' in latest:
        cleaned = latest['cleaned_text']
        print(f"✅ cleaned_text: PRESENT ({len(cleaned)} chars)")
    else:
        print(f"ℹ️  cleaned_text: Not present")
    
    print()
    
    # Check tokens
    if 'tokens' in latest:
        tokens = latest['tokens']
        token_count = latest.get('token_count', len(tokens))
        print(f"✅ tokens: PRESENT (array with {token_count} tokens)")
        print(f"   First 10 tokens: {tokens[:10]}")
        print(f"   Sample tokens: {tokens[:5]}")
    else:
        print(f"❌ tokens: MISSING")
    
    print()
    
    # Check token_count
    if 'token_count' in latest:
        print(f"✅ token_count: {latest['token_count']}")
    else:
        print(f"❌ token_count: MISSING")
    
    print()
    
    # Check other fields
    print("Other fields present:")
    for key in ['stt_confidence', 'embedding', 'embedding_present', 'pii_metadata', 'pii_vault_id']:
        if key in latest:
            value = latest[key]
            if key == 'embedding':
                print(f"  - {key}: {type(value).__name__} with {len(value) if value else 0} dimensions")
            else:
                print(f"  - {key}: {value}")
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    has_text = 'original_text' in latest or 'redacted_text' in latest
    has_tokens = 'tokens' in latest
    
    if has_text and has_tokens:
        print("✅ SUCCESS: Both text and tokens are stored in MongoDB!")
    elif has_text and not has_tokens:
        print("⚠️  WARNING: Text is stored but tokens are MISSING!")
        print("   This might indicate an issue with the text processor.")
    elif not has_text and has_tokens:
        print("⚠️  WARNING: Tokens are stored but text is MISSING!")
    else:
        print("❌ ERROR: Neither text nor tokens are stored!")
    
    print()
    
    # Close connection
    client.close()

if __name__ == "__main__":
    asyncio.run(check_mongodb_storage())
