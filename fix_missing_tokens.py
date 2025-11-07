"""
Fix Missing Tokens Script
Adds tokens to existing MongoDB documents that have text but no tokens.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from motor.motor_asyncio import AsyncIOMotorClient
from processors.text_processor import get_text_processor

async def fix_missing_tokens(dry_run=True):
    """
    Find and fix answers that have text but no tokens.
    
    Args:
        dry_run: If True, only report what would be fixed without making changes
    """
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["interview_db"]
    
    print("=" * 70)
    print("FIX MISSING TOKENS SCRIPT")
    print("=" * 70)
    print(f"Mode: {'DRY RUN (no changes)' if dry_run else 'LIVE (will modify database)'}")
    print()
    
    # Find answers without tokens but with text
    query = {
        "$or": [
            {"tokens": {"$exists": False}},
            {"tokens": []},
            {"tokens": None}
        ],
        "$or": [
            {"original_text": {"$exists": True, "$ne": "", "$ne": None}},
            {"cleaned_text": {"$exists": True, "$ne": "", "$ne": None}}
        ]
    }
    
    # Simplified query for better MongoDB compatibility
    query = {
        "tokens": {"$exists": False},
        "original_text": {"$exists": True}
    }
    
    total_count = await db.answers.count_documents(query)
    print(f"📊 Found {total_count} documents missing tokens")
    
    if total_count == 0:
        print("✅ All documents already have tokens!")
        client.close()
        return
    
    if dry_run:
        print("\n🔍 DRY RUN - Showing what would be fixed:")
        print("-" * 70)
    else:
        print("\n🔧 FIXING documents:")
        print("-" * 70)
        
    # Get text processor
    text_processor = get_text_processor()
    fixed_count = 0
    error_count = 0
    
    cursor = db.answers.find(query).limit(100)  # Limit for safety
    
    async for doc in cursor:
        try:
            # Get text (prefer original_text, fallback to cleaned_text)
            text = doc.get("original_text") or doc.get("cleaned_text")
            
            if not text:
                print(f"⚠️  {doc['_id']}: No text found, skipping")
                continue
            
            # Process text to get tokens
            text_result = await text_processor.process_text(
                text,
                compute_embedding=False,
                lowercase_tokens=False
            )
            
            tokens = text_result["tokens"]
            token_count = text_result["token_count"]
            
            if dry_run:
                print(f"Would fix {doc['_id']}:")
                print(f"  Text: {text[:50]}...")
                print(f"  Would add {token_count} tokens")
                print(f"  Sample: {tokens[:5]}")
                print()
            else:
                # Update document
                update_data = {
                    "tokens": tokens,
                    "token_count": token_count
                }
                
                # Add cleaned_text if not present
                if "cleaned_text" not in doc:
                    update_data["cleaned_text"] = text_result["cleaned_text"]
                
                await db.answers.update_one(
                    {"_id": doc["_id"]},
                    {"$set": update_data}
                )
                
                print(f"✓ Fixed {doc['_id']}: added {token_count} tokens")
            
            fixed_count += 1
            
        except Exception as e:
            error_count += 1
            print(f"✗ Failed to fix {doc.get('_id', 'unknown')}: {e}")
    
    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    if dry_run:
        print(f"Would fix: {fixed_count} documents")
        print(f"Errors: {error_count}")
        print()
        print("To actually apply fixes, run:")
        print("  python fix_missing_tokens.py --apply")
    else:
        print(f"✅ Fixed: {fixed_count} documents")
        print(f"❌ Errors: {error_count}")
        print()
        print("Verify in MongoDB:")
        print("  db.answers.find({tokens: {$exists: true}}).count()")
    
    print()
    client.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Fix missing tokens in MongoDB")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually apply fixes (default is dry-run)"
    )
    
    args = parser.parse_args()
    
    asyncio.run(fix_missing_tokens(dry_run=not args.apply))
