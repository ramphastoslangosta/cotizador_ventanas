# security/auth_enhancements.py - Enhanced authentication security
import secrets
import hashlib
import time
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Set
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

class AuthSecurityEnhancer:
    """
    Enhanced authentication security features including:
    - Login attempt tracking and brute force protection
    - Session security enhancements
    - Password policies
    - Account lockout mechanisms
    """
    
    def __init__(self):
        # In production, use Redis or database for persistence
        self.failed_attempts: Dict[str, Dict] = {}
        self.locked_accounts: Dict[str, float] = {}
        
        # Security configuration
        self.max_failed_attempts = 5
        self.lockout_duration = 900  # 15 minutes
        self.attempt_window = 300    # 5 minutes
        
    def check_brute_force_protection(self, email: str) -> bool:
        """
        Check if account is locked due to brute force attempts
        Returns True if account is accessible, False if locked
        """
        current_time = time.time()
        
        # Check if account is currently locked
        if email in self.locked_accounts:
            lock_end_time = self.locked_accounts[email]
            if current_time < lock_end_time:
                remaining_time = int((lock_end_time - current_time) / 60)
                logger.warning(f"Account {email} is locked. {remaining_time} minutes remaining.")
                return False
            else:
                # Lock expired, remove from locked accounts
                del self.locked_accounts[email]
                # Reset failed attempts
                if email in self.failed_attempts:
                    del self.failed_attempts[email]
        
        return True
    
    def record_failed_login(self, email: str, ip_address: str) -> None:
        """
        Record a failed login attempt and potentially lock the account
        """
        current_time = time.time()
        
        # Initialize tracking for this email if not exists
        if email not in self.failed_attempts:
            self.failed_attempts[email] = {
                'attempts': [],
                'ips': set()
            }
        
        account_data = self.failed_attempts[email]
        
        # Clean old attempts outside the window
        window_start = current_time - self.attempt_window
        account_data['attempts'] = [
            attempt for attempt in account_data['attempts'] 
            if attempt > window_start
        ]
        
        # Add current attempt
        account_data['attempts'].append(current_time)
        account_data['ips'].add(ip_address)
        
        # Check if we should lock the account
        if len(account_data['attempts']) >= self.max_failed_attempts:
            self.locked_accounts[email] = current_time + self.lockout_duration
            logger.warning(f"Account {email} locked due to {self.max_failed_attempts} failed attempts from IPs: {account_data['ips']}")
    
    def record_successful_login(self, email: str) -> None:
        """
        Record successful login and clear any failed attempts
        """
        if email in self.failed_attempts:
            del self.failed_attempts[email]
        if email in self.locked_accounts:
            del self.locked_accounts[email]
    
    def validate_password_strength(self, password: str) -> bool:
        """
        Validate password meets security requirements
        """
        if len(password) < 8:
            return False
        
        # Check for at least one letter, one number
        has_letter = any(c.isalpha() for c in password)
        has_number = any(c.isdigit() for c in password)
        
        return has_letter and has_number
    
    def generate_secure_token(self, length: int = 32) -> str:
        """
        Generate cryptographically secure token
        """
        return secrets.token_urlsafe(length)
    
    def is_token_expired(self, session_created: datetime, max_age_hours: int = 2) -> bool:
        """
        Check if session token is expired
        """
        if not session_created.tzinfo:
            session_created = session_created.replace(tzinfo=timezone.utc)
        
        expiry_time = session_created + timedelta(hours=max_age_hours)
        return datetime.now(timezone.utc) > expiry_time
    
    def get_security_headers(self) -> Dict[str, str]:
        """
        Get recommended security headers for authentication responses
        """
        return {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'Cache-Control': 'no-store, no-cache, must-revalidate',
            'Pragma': 'no-cache'
        }

class SessionManager:
    """
    Enhanced session management with security features
    """
    
    def __init__(self):
        self.active_sessions: Dict[str, Dict] = {}
        self.session_cleanup_interval = 3600  # 1 hour
        self.last_cleanup = time.time()
    
    def create_session(self, user_id: str, user_agent: str, ip_address: str) -> Dict[str, str]:
        """
        Create a new secure session
        """
        token = secrets.token_urlsafe(32)
        session_id = secrets.token_urlsafe(16)
        
        session_data = {
            'token': token,
            'user_id': user_id,
            'created_at': datetime.now(timezone.utc),
            'last_activity': datetime.now(timezone.utc),
            'user_agent': user_agent,
            'ip_address': ip_address,
            'session_id': session_id
        }
        
        self.active_sessions[token] = session_data
        self._cleanup_old_sessions()
        
        return {
            'token': token,
            'session_id': session_id
        }
    
    def validate_session(self, token: str, user_agent: str, ip_address: str) -> Optional[Dict]:
        """
        Validate session with security checks
        """
        if token not in self.active_sessions:
            return None
        
        session = self.active_sessions[token]
        
        # Check if session is expired (2 hours default)
        if self._is_session_expired(session):
            del self.active_sessions[token]
            return None
        
        # Security check: validate user agent and IP consistency
        if session['user_agent'] != user_agent:
            logger.warning(f"User agent mismatch for session {token[:8]}...")
            del self.active_sessions[token]
            return None
        
        if session['ip_address'] != ip_address:
            logger.warning(f"IP address change detected for session {token[:8]}...")
            # In production, you might want to invalidate or require re-authentication
            # For now, we'll log but allow (could be mobile network switch)
        
        # Update last activity
        session['last_activity'] = datetime.now(timezone.utc)
        
        return session
    
    def invalidate_session(self, token: str) -> bool:
        """
        Invalidate a specific session
        """
        if token in self.active_sessions:
            del self.active_sessions[token]
            return True
        return False
    
    def invalidate_all_user_sessions(self, user_id: str) -> int:
        """
        Invalidate all sessions for a specific user
        """
        sessions_to_remove = []
        for token, session in self.active_sessions.items():
            if session['user_id'] == user_id:
                sessions_to_remove.append(token)
        
        for token in sessions_to_remove:
            del self.active_sessions[token]
        
        return len(sessions_to_remove)
    
    def _is_session_expired(self, session: Dict, max_age_hours: int = 2) -> bool:
        """
        Check if session is expired
        """
        created_at = session['created_at']
        if not created_at.tzinfo:
            created_at = created_at.replace(tzinfo=timezone.utc)
        
        expiry_time = created_at + timedelta(hours=max_age_hours)
        return datetime.now(timezone.utc) > expiry_time
    
    def _cleanup_old_sessions(self):
        """
        Cleanup expired sessions periodically
        """
        current_time = time.time()
        if current_time - self.last_cleanup < self.session_cleanup_interval:
            return
        
        expired_tokens = []
        for token, session in self.active_sessions.items():
            if self._is_session_expired(session):
                expired_tokens.append(token)
        
        for token in expired_tokens:
            del self.active_sessions[token]
        
        self.last_cleanup = current_time
        
        if expired_tokens:
            logger.info(f"Cleaned up {len(expired_tokens)} expired sessions")

# Global instances
auth_security = AuthSecurityEnhancer()
session_manager = SessionManager()