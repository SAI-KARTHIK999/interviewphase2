"""
Data Retention Management Script
Verify TTL index, view deletion logs, and manage data retention policy
"""
import os
from datetime import datetime, timedelta
from pymongo import MongoClient

# Constants
RETENTION_DAYS = 30
RETENTION_SECONDS = RETENTION_DAYS * 24 * 60 * 60

def connect_db():
    """Connect to MongoDB"""
    try:
        client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=2000)
        client.server_info()
        db = client['interview_db']
        return db, client
    except Exception as e:
        print(f"✗ MongoDB connection failed: {e}")
        return None, None

def check_ttl_index(db):
    """Verify TTL index is properly configured"""
    print("\n" + "="*60)
    print("CHECKING TTL INDEX")
    print("="*60)
    
    try:
        interviews = db['interviews']
        indexes = list(interviews.list_indexes())
        
        ttl_found = False
        for index in indexes:
            if 'expireAfterSeconds' in index:
                ttl_found = True
                field_name = list(index['key'].keys())[0]
                expire_seconds = index['expireAfterSeconds']
                expire_days = expire_seconds / (24 * 60 * 60)
                
                print(f"✓ TTL Index Found")
                print(f"  Field: {field_name}")
                print(f"  Expiration: {expire_seconds} seconds ({expire_days:.0f} days)")
                print(f"  Status: {'✓ ACTIVE' if expire_days == RETENTION_DAYS else '⚠️  DIFFERENT FROM CONFIG'}")
        
        if not ttl_found:
            print("✗ No TTL index found!")
            print("\nTo create TTL index, run:")
            print(f"  db.interviews.createIndex({{\"createdAt\": 1}}, {{expireAfterSeconds: {RETENTION_SECONDS}}})")
            return False
        
        return True
    except Exception as e:
        print(f"✗ Error checking TTL index: {e}")
        return False

def view_data_with_countdown(db):
    """View all interview data with days remaining until deletion"""
    print("\n" + "="*60)
    print("INTERVIEW DATA WITH DELETION COUNTDOWN")
    print("="*60)
    
    try:
        interviews = db['interviews']
        total_count = interviews.count_documents({})
        
        print(f"Total records: {total_count}\n")
        
        if total_count == 0:
            print("No interview data found.")
            return
        
        # Get all records sorted by creation date
        records = list(interviews.find({}).sort('createdAt', -1))
        
        print(f"{'ID':<25} {'Created':<20} {'Days Left':<12} {'Deletion Date':<20}")
        print("-" * 85)
        
        for record in records:
            record_id = record.get('id', 'N/A')[:24]
            
            if 'createdAt' in record:
                created = record['createdAt']
                deletion_date = created + timedelta(days=RETENTION_DAYS)
                days_left = (deletion_date - datetime.utcnow()).days
                
                # Color code based on urgency
                if days_left < 0:
                    status = "⚠️  EXPIRED"
                elif days_left <= 3:
                    status = f"🔴 {days_left} days"
                elif days_left <= 7:
                    status = f"🟡 {days_left} days"
                else:
                    status = f"🟢 {days_left} days"
                
                created_str = created.strftime('%Y-%m-%d %H:%M')
                deletion_str = deletion_date.strftime('%Y-%m-%d %H:%M')
                
                print(f"{record_id:<25} {created_str:<20} {status:<12} {deletion_str:<20}")
            else:
                print(f"{record_id:<25} {'Old record':<20} {'N/A':<12} {'N/A':<20}")
        
    except Exception as e:
        print(f"✗ Error viewing data: {e}")

def view_deletion_logs(db):
    """View deletion logs"""
    print("\n" + "="*60)
    print("DELETION LOGS")
    print("="*60)
    
    try:
        deletion_log = db['deletion_log']
        log_count = deletion_log.count_documents({})
        
        print(f"Total deletion events: {log_count}\n")
        
        if log_count == 0:
            print("No deletion logs found.")
            return
        
        # Get recent deletion logs
        logs = list(deletion_log.find({}).sort('deleted_at', -1).limit(20))
        
        print(f"{'Deleted At':<20} {'User ID':<25} {'Type':<10} {'Count':<8}")
        print("-" * 70)
        
        for log in logs:
            deleted_at = log.get('deleted_at')
            if isinstance(deleted_at, datetime):
                deleted_str = deleted_at.strftime('%Y-%m-%d %H:%M')
            else:
                deleted_str = str(deleted_at)[:19]
            
            user_id = str(log.get('user_id', 'N/A'))[:24]
            deletion_type = log.get('deletion_type', 'N/A')
            deleted_count = log.get('deleted_count', 0)
            
            print(f"{deleted_str:<20} {user_id:<25} {deletion_type:<10} {deleted_count:<8}")
        
    except Exception as e:
        print(f"✗ Error viewing logs: {e}")

def create_ttl_index(db):
    """Manually create or update TTL index"""
    print("\n" + "="*60)
    print("CREATING/UPDATING TTL INDEX")
    print("="*60)
    
    try:
        interviews = db['interviews']
        
        # Drop existing TTL index if any
        try:
            indexes = list(interviews.list_indexes())
            for index in indexes:
                if 'expireAfterSeconds' in index:
                    index_name = index['name']
                    interviews.drop_index(index_name)
                    print(f"✓ Dropped old TTL index: {index_name}")
        except Exception as e:
            print(f"Note: {e}")
        
        # Create new TTL index
        result = interviews.create_index("createdAt", expireAfterSeconds=RETENTION_SECONDS)
        print(f"✓ TTL index created: {result}")
        print(f"✓ Documents will auto-delete {RETENTION_DAYS} days after createdAt field")
        
        return True
    except Exception as e:
        print(f"✗ Error creating TTL index: {e}")
        return False

def cleanup_old_videos(db):
    """Find and remove orphaned video files"""
    print("\n" + "="*60)
    print("CLEANUP ORPHANED VIDEO FILES")
    print("="*60)
    
    upload_dir = os.path.join(os.path.dirname(__file__), 'uploads')
    
    if not os.path.exists(upload_dir):
        print("✗ Upload directory not found")
        return
    
    try:
        interviews = db['interviews']
        
        # Get all video filenames from database
        db_videos = set()
        for record in interviews.find({}, {'video_filename': 1}):
            if 'video_filename' in record:
                db_videos.add(record['video_filename'])
        
        # Get all video files from disk
        disk_videos = [f for f in os.listdir(upload_dir) if f.endswith(('.webm', '.mp4', '.avi'))]
        
        # Find orphaned files
        orphaned = [f for f in disk_videos if f not in db_videos]
        
        print(f"Total videos on disk: {len(disk_videos)}")
        print(f"Videos in database: {len(db_videos)}")
        print(f"Orphaned files: {len(orphaned)}")
        
        if orphaned:
            print("\nOrphaned files:")
            for vid in orphaned[:10]:  # Show first 10
                print(f"  - {vid}")
            
            if len(orphaned) > 10:
                print(f"  ... and {len(orphaned) - 10} more")
            
            response = input("\nDelete orphaned files? (yes/no): ")
            if response.lower() == 'yes':
                deleted = 0
                for vid in orphaned:
                    try:
                        os.remove(os.path.join(upload_dir, vid))
                        deleted += 1
                    except Exception as e:
                        print(f"✗ Failed to delete {vid}: {e}")
                print(f"✓ Deleted {deleted} orphaned files")
        
    except Exception as e:
        print(f"✗ Error during cleanup: {e}")

def main_menu():
    """Interactive menu"""
    db, client = connect_db()
    
    if db is None:
        print("\n⚠️  Cannot continue without database connection")
        return
    
    while True:
        print("\n" + "="*60)
        print("DATA RETENTION MANAGEMENT")
        print("="*60)
        print("1. Check TTL Index Status")
        print("2. View Data with Deletion Countdown")
        print("3. View Deletion Logs")
        print("4. Create/Update TTL Index")
        print("5. Cleanup Orphaned Video Files")
        print("6. Exit")
        print("="*60)
        
        choice = input("\nSelect option (1-6): ").strip()
        
        if choice == '1':
            check_ttl_index(db)
        elif choice == '2':
            view_data_with_countdown(db)
        elif choice == '3':
            view_deletion_logs(db)
        elif choice == '4':
            create_ttl_index(db)
        elif choice == '5':
            cleanup_old_videos(db)
        elif choice == '6':
            print("\n✓ Goodbye!")
            client.close()
            break
        else:
            print("Invalid option. Please try again.")

if __name__ == "__main__":
    print("\n🗑️  AI INTERVIEW - DATA RETENTION MANAGER\n")
    main_menu()
