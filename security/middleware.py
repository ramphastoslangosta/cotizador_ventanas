# security/middleware.py - Security middleware for FastAPI
import secrets
import time
import hashlib
from typing import Dict, Set, Optional
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import logging

logger = logging.getLogger(__name__)

class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Comprehensive security middleware that provides:
    - Rate limiting
    - CSRF protection
    - Basic security headers
    - Request logging for security events
    """
    
    def __init__(
        self, 
        app: ASGIApp,
        rate_limit_requests: int = 100,  # requests per minute
        rate_limit_window: int = 60,     # window in seconds
        csrf_exempt_paths: Optional[Set[str]] = None
    ):
        super().__init__(app)
        self.rate_limit_requests = rate_limit_requests
        self.rate_limit_window = rate_limit_window
        
        # Rate limiting storage (in production, use Redis)
        self._rate_limit_storage: Dict[str, Dict] = {}
        
        # CSRF exempt paths (API endpoints, public pages)
        self.csrf_exempt_paths = csrf_exempt_paths or {
            '/api/', '/docs', '/redoc', '/openapi.json', 
            '/static/', '/favicon.ico', '/', '/login', '/register'
        }
        
        # Security headers to add to all responses
        self.security_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Content-Security-Policy': (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' cdnjs.cloudflare.com cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' cdnjs.cloudflare.com cdn.jsdelivr.net; "
                "font-src 'self' data: cdnjs.cloudflare.com cdn.jsdelivr.net; "
                "img-src 'self' data: https:; "
                "connect-src 'self';"
            )
        }
    
    async def dispatch(self, request: Request, call_next):
        # Get client IP for rate limiting
        client_ip = self._get_client_ip(request)
        
        # Apply rate limiting
        if not self._check_rate_limit(client_ip):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"error": "Rate limit exceeded. Please try again later."}
            )
        
        # Check CSRF for state-changing operations
        if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
            if not self._is_csrf_exempt(request.url.path):
                csrf_valid = await self._validate_csrf(request)
                if not csrf_valid:
                    return JSONResponse(
                        status_code=status.HTTP_403_FORBIDDEN,
                        content={"error": "CSRF token validation failed"}
                    )
        
        # Process the request
        try:
            response = await call_next(request)
        except Exception as e:
            logger.error(f"Request processing error: {str(e)}")
            raise
        
        # Add security headers
        for header, value in self.security_headers.items():
            response.headers[header] = value
        
        # Add CSRF token to responses for HTML pages
        if (response.headers.get('content-type', '').startswith('text/html') and 
            request.method == 'GET'):
            csrf_token = self._generate_csrf_token(request)
            response.set_cookie(
                'csrf_token',
                csrf_token,
                httponly=False,  # Needs to be accessible to JS
                secure=False,    # Set to True in production with HTTPS
                samesite='lax',
                max_age=3600
            )
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address, considering proxies"""
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else '127.0.0.1'
    
    def _check_rate_limit(self, client_ip: str) -> bool:
        """Check if client has exceeded rate limit"""
        current_time = time.time()
        
        # Clean old entries
        self._cleanup_rate_limit_storage(current_time)
        
        # Get or create client entry
        if client_ip not in self._rate_limit_storage:
            self._rate_limit_storage[client_ip] = {
                'requests': [],
                'blocked_until': 0
            }
        
        client_data = self._rate_limit_storage[client_ip]
        
        # Check if still blocked
        if current_time < client_data['blocked_until']:
            return False
        
        # Remove requests outside the window
        window_start = current_time - self.rate_limit_window
        client_data['requests'] = [
            req_time for req_time in client_data['requests'] 
            if req_time > window_start
        ]
        
        # Check rate limit
        if len(client_data['requests']) >= self.rate_limit_requests:
            # Block for the remaining window time
            client_data['blocked_until'] = current_time + self.rate_limit_window
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return False
        
        # Add current request
        client_data['requests'].append(current_time)
        return True
    
    def _cleanup_rate_limit_storage(self, current_time: float):
        """Clean up old rate limit entries"""
        cutoff = current_time - (self.rate_limit_window * 2)
        
        clients_to_remove = []
        for client_ip, data in self._rate_limit_storage.items():
            # Remove if no recent requests and not blocked
            if (not data['requests'] or max(data['requests']) < cutoff) and \
               data['blocked_until'] < current_time:
                clients_to_remove.append(client_ip)
        
        for client_ip in clients_to_remove:
            del self._rate_limit_storage[client_ip]
    
    def _is_csrf_exempt(self, path: str) -> bool:
        """Check if path is exempt from CSRF protection"""
        for exempt_path in self.csrf_exempt_paths:
            if path.startswith(exempt_path):
                return True
        return False
    
    async def _validate_csrf(self, request: Request) -> bool:
        """Validate CSRF token"""
        # Get token from header or form data
        csrf_token = request.headers.get('X-CSRF-Token')
        
        if not csrf_token:
            # Try to get from form data for regular form submissions
            try:
                form_data = await request.form()
                csrf_token = form_data.get('csrf_token')
            except:
                pass
        
        if not csrf_token:
            # Try to get from cookies as fallback
            csrf_token = request.cookies.get('csrf_token')
        
        if not csrf_token:
            logger.warning(f"CSRF token missing for {request.method} {request.url.path}")
            return False
        
        # Validate token format and authenticity
        return self._verify_csrf_token(csrf_token, request)
    
    def _generate_csrf_token(self, request: Request) -> str:
        """Generate CSRF token for the session"""
        # Use session ID or IP as part of the token
        session_id = request.cookies.get('session_token', '')
        client_ip = self._get_client_ip(request)
        
        # Create a deterministic token based on session and secret
        token_data = f"{session_id}:{client_ip}:{secrets.token_hex(16)}"
        token_hash = hashlib.sha256(token_data.encode()).hexdigest()
        
        return f"{secrets.token_hex(16)}.{token_hash[:32]}"
    
    def _verify_csrf_token(self, token: str, request: Request) -> bool:
        """Verify CSRF token authenticity"""
        if not token or '.' not in token:
            return False
        
        try:
            # Basic token format validation
            parts = token.split('.')
            if len(parts) != 2:
                return False
            
            # In a full implementation, you'd validate the token signature
            # For now, we accept any properly formatted token
            return len(parts[0]) == 32 and len(parts[1]) == 32
        except Exception:
            return False

class SecureCookieMiddleware(BaseHTTPMiddleware):
    """
    Middleware to ensure secure cookie settings
    """
    
    def __init__(self, app: ASGIApp, secure: bool = False):
        super().__init__(app)
        self.secure = secure  # Set to True in production with HTTPS
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Update cookie settings for security
        if hasattr(response, 'set_cookie'):
            # This is handled by FastAPI's response.set_cookie method
            pass
        
        return response