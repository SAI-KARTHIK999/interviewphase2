"""
Immutable Audit Logging System
Write-only audit logs for security-sensitive operations
"""

import os
import hashlib
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from bson import ObjectId
from flask import request, g

logger = logging.getLogger(__name__)


class AuditLogger:
    """Immutable audit logger for security events"""
    
    def __init__(self, db):
        """
        Initialize audit logger
        
        Args:
            db: MongoDB database instance
        """
        self.db = db
        self.collection = db.access_audit_logs
        self._ensure_indexes()
        self._last_hash = None
    
    def _ensure_indexes(self):
        """Create indexes for audit logs"""
        try:
            # Indexes for common queries
            self.collection.create_index("actor_id")
            self.collection.create_index("action")
            self.collection.create_index("timestamp")
            self.collection.create_index([("actor_id", 1), ("timestamp", -1)])
            self.collection.create_index([("action", 1), ("timestamp", -1)])
            self.collection.create_index("target_id")
            self.collection.create_index("success")
            
            logger.info("✓ Audit log indexes created")
        except Exception as e:
            logger.warning(f"Audit log index creation warning: {e}")
    
    def _compute_hash(self, log_entry: Dict) -> str:
        """
        Compute tamper-evident hash for log entry
        Includes previous hash for chain integrity
        """
        # Create deterministic string from log entry
        hash_input = f"{log_entry['timestamp'].isoformat()}" \
                    f"{log_entry['actor_id']}" \
                    f"{log_entry['action']}" \
                    f"{log_entry.get('target_id', '')}" \
                    f"{self._last_hash or ''}"
        
        return hashlib.sha256(hash_input.encode('utf-8')).hexdigest()
    
    def log(
        self,
        action: str,
        success: bool = True,
        actor_id: Optional[str] = None,
        actor_roles: Optional[List[str]] = None,
        target_collection: Optional[str] = None,
        target_id: Optional[str] = None,
        fields_accessed: Optional[List[str]] = None,
        justification: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> ObjectId:
        """
        Write an audit log entry (IMMUTABLE)
        
        Args:
            action: Action performed (read/write/decrypt/delete/role_assign/retention_run)
            success: Whether operation succeeded
            actor_id: User or service performing action
            actor_roles: Roles of the actor
            target_collection: Database collection accessed
            target_id: ID of specific document accessed
            fields_accessed: List of fields accessed
            justification: Reason for access (required for sensitive ops)
            metadata: Additional context
        
        Returns:
            ObjectId of audit log entry
        """
        try:
            # Extract actor info from Flask context if not provided
            if actor_id is None:
                current_user = getattr(g, 'current_user', None)
                if current_user:
                    actor_id = current_user.get('user_id')
                    actor_roles = current_user.get('roles', [])
            
            # Extract request info
            ip_address = None
            user_agent = None
            if request:
                ip_address = request.remote_addr
                user_agent = request.headers.get('User-Agent')
            
            timestamp = datetime.utcnow()
            
            # Create log entry
            log_entry = {
                "actor_id": actor_id or "anonymous",
                "actor_roles": actor_roles or [],
                "action": action,
                "target_collection": target_collection,
                "target_id": target_id,
                "fields_accessed": fields_accessed or [],
                "justification": justification,
                "success": success,
                "ip": ip_address,
                "user_agent": user_agent,
                "timestamp": timestamp,
                "metadata": metadata or {}
            }
            
            # Compute tamper-evident hash
            entry_hash = self._compute_hash(log_entry)
            log_entry["entry_hash"] = entry_hash
            log_entry["prev_hash"] = self._last_hash
            
            # Insert (write-only, no updates allowed)
            result = self.collection.insert_one(log_entry)
            
            # Update last hash for chain
            self._last_hash = entry_hash
            
            logger.debug(f"Audit log created: {action} by {actor_id}")
            
            return result.inserted_id
        
        except Exception as e:
            logger.error(f"CRITICAL: Failed to write audit log: {e}")
            # Audit log failure is critical - consider alerting
            raise
    
    def log_read(
        self,
        target_collection: str,
        target_id: str,
        fields_accessed: List[str],
        success: bool = True
    ) -> ObjectId:
        """Log read access to sensitive data"""
        return self.log(
            action="read",
            target_collection=target_collection,
            target_id=target_id,
            fields_accessed=fields_accessed,
            success=success
        )
    
    def log_write(
        self,
        target_collection: str,
        target_id: str,
        fields_modified: List[str],
        success: bool = True
    ) -> ObjectId:
        """Log write/modification of data"""
        return self.log(
            action="write",
            target_collection=target_collection,
            target_id=target_id,
            fields_accessed=fields_modified,
            success=success
        )
    
    def log_decrypt(
        self,
        target_collection: str,
        target_id: str,
        fields_decrypted: List[str],
        justification: str,
        success: bool = True
    ) -> ObjectId:
        """Log decryption of encrypted fields (REQUIRES JUSTIFICATION)"""
        if not justification or len(justification.strip()) < 10:
            raise ValueError("Decryption requires detailed justification (min 10 chars)")
        
        return self.log(
            action="decrypt",
            target_collection=target_collection,
            target_id=target_id,
            fields_accessed=fields_decrypted,
            justification=justification,
            success=success
        )
    
    def log_delete(
        self,
        target_collection: str,
        target_id: str,
        reason: Optional[str] = None,
        success: bool = True
    ) -> ObjectId:
        """Log deletion of data"""
        return self.log(
            action="delete",
            target_collection=target_collection,
            target_id=target_id,
            justification=reason,
            success=success
        )
    
    def log_role_assign(
        self,
        target_user_id: str,
        roles_assigned: List[str],
        justification: str,
        success: bool = True
    ) -> ObjectId:
        """Log role assignment changes"""
        return self.log(
            action="role_assign",
            target_id=target_user_id,
            metadata={"roles_assigned": roles_assigned},
            justification=justification,
            success=success
        )
    
    def log_access_request(
        self,
        request_type: str,
        reason: str,
        target_resource: Optional[str] = None,
        success: bool = True
    ) -> ObjectId:
        """Log access elevation requests"""
        return self.log(
            action="access_request",
            target_id=target_resource,
            justification=reason,
            metadata={"request_type": request_type},
            success=success
        )
    
    def log_retention_run(
        self,
        records_deleted: int,
        success: bool = True
    ) -> ObjectId:
        """Log automated data retention operations"""
        return self.log(
            action="retention_run",
            actor_id="system:retention_job",
            actor_roles=["system"],
            metadata={"records_deleted": records_deleted},
            success=success
        )
    
    def query_logs(
        self,
        actor_id: Optional[str] = None,
        action: Optional[str] = None,
        target_id: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        success: Optional[bool] = None,
        limit: int = 100,
        skip: int = 0
    ) -> List[Dict]:
        """
        Query audit logs (READ-ONLY, admin access required)
        
        Returns:
            List of audit log entries
        """
        query = {}
        
        if actor_id:
            query["actor_id"] = actor_id
        
        if action:
            query["action"] = action
        
        if target_id:
            query["target_id"] = target_id
        
        if success is not None:
            query["success"] = success
        
        if from_date or to_date:
            query["timestamp"] = {}
            if from_date:
                query["timestamp"]["$gte"] = from_date
            if to_date:
                query["timestamp"]["$lte"] = to_date
        
        # Query with pagination
        cursor = self.collection.find(query) \
                               .sort("timestamp", -1) \
                               .skip(skip) \
                               .limit(limit)
        
        logs = list(cursor)
        
        # Log the audit query itself
        try:
            self.log(
                action="audit_query",
                metadata={
                    "query_params": {
                        "actor_id": actor_id,
                        "action": action,
                        "from_date": from_date.isoformat() if from_date else None,
                        "to_date": to_date.isoformat() if to_date else None
                    },
                    "results_count": len(logs)
                },
                success=True
            )
        except:
            pass  # Don't fail query if logging fails
        
        return logs
    
    def verify_chain_integrity(self, limit: int = 1000) -> bool:
        """
        Verify tamper-evident hash chain
        
        Returns:
            True if chain is intact, False if tampered
        """
        logs = list(self.collection.find().sort("timestamp", 1).limit(limit))
        
        prev_hash = None
        for log_entry in logs:
            # Check if prev_hash matches
            if log_entry.get("prev_hash") != prev_hash:
                logger.error(f"Hash chain broken at entry {log_entry['_id']}")
                return False
            
            # Recompute hash
            computed_hash = self._compute_hash(log_entry)
            stored_hash = log_entry.get("entry_hash")
            
            if computed_hash != stored_hash:
                logger.error(f"Hash mismatch at entry {log_entry['_id']}")
                return False
            
            prev_hash = stored_hash
        
        logger.info(f"✓ Audit log chain verified ({len(logs)} entries)")
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Get audit log statistics"""
        total_logs = self.collection.count_documents({})
        
        # Count by action
        action_counts = {}
        for action in ["read", "write", "decrypt", "delete", "role_assign", "retention_run"]:
            count = self.collection.count_documents({"action": action})
            action_counts[action] = count
        
        # Recent failed operations
        failed_recent = self.collection.count_documents({
            "success": False,
            "timestamp": {"$gte": datetime.utcnow() - timedelta(hours=24)}
        })
        
        return {
            "total_logs": total_logs,
            "action_counts": action_counts,
            "failed_operations_24h": failed_recent,
            "chain_verified": self.verify_chain_integrity(limit=100)
        }


# Global audit logger instance
_audit_logger: Optional[AuditLogger] = None

def init_audit_logger(db):
    """Initialize global audit logger"""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger(db)
    return _audit_logger

def get_audit_logger() -> Optional[AuditLogger]:
    """Get initialized audit logger"""
    return _audit_logger


# Convenience functions
def audit_log(action: str, **kwargs):
    """Convenience function to log audit event"""
    logger_instance = get_audit_logger()
    if logger_instance:
        return logger_instance.log(action, **kwargs)
    else:
        logger.warning("Audit logger not initialized")
        return None


from datetime import timedelta
