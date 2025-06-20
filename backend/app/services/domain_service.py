"""
Domain validation service for email domain restrictions.
"""
import re
import logging
from typing import Optional
from fastapi import HTTPException

from ..config import Settings

logger = logging.getLogger(__name__)


class DomainService:
    """Service for validating email domains against allowed patterns."""
    
    def __init__(self, settings: Settings):
        """
        Initialize domain service with settings.
        
        Args:
            settings: Application settings containing domain regex
        """
        self.settings = settings
        self._compiled_regex: Optional[re.Pattern] = None
        self._compile_domain_regex()
    
    def _compile_domain_regex(self) -> None:
        """Compile the domain regex pattern for validation."""
        try:
            self._compiled_regex = re.compile(self.settings.allowed_email_domain_regex)
            logger.debug("Domain regex compiled successfully")
        except re.error as e:
            logger.error(f"Invalid domain regex pattern: {e}")
            # Fall back to allow all domains
            self._compiled_regex = re.compile(".*")
            logger.warning("Using fallback regex to allow all domains")
    
    def validate_email_domain(self, email: str) -> bool:
        """
        Validate email domain against allowed pattern.
        
        Args:
            email: Email address to validate
            
        Returns:
            True if email domain is allowed, False otherwise
        """
        if not email:
            logger.warning("Empty email provided for domain validation")
            return False
        
        # If no regex pattern is set or it's the default ".*", allow all
        if (not self.settings.allowed_email_domain_regex or 
            self.settings.allowed_email_domain_regex == ".*"):
            return True
        
        try:
            is_valid = bool(self._compiled_regex.match(email))
            if not is_valid:
                logger.info(f"Email domain validation failed for domain pattern")
            return is_valid
        except Exception as e:
            logger.error(f"Error during domain validation: {type(e).__name__}")
            # In case of error, be permissive (allow the email)
            return True
    
    def validate_and_raise(self, email: str) -> None:
        """
        Validate email domain and raise HTTPException if invalid.
        
        Args:
            email: Email address to validate
            
        Raises:
            HTTPException: If email domain is not allowed
        """
        if not email:
            raise HTTPException(status_code=400, detail="Email address is required")
        
        if not self.validate_email_domain(email):
            logger.warning("Access denied: email domain not allowed")
            raise HTTPException(status_code=403, detail="Email domain not allowed")
    
    def get_domain_from_email(self, email: str) -> str:
        """
        Extract domain from email address.
        
        Args:
            email: Email address
            
        Returns:
            Domain part of the email address
        """
        if not email or "@" not in email:
            return ""
        
        return email.split("@")[-1].lower()
    
    def is_domain_configured(self) -> bool:
        """
        Check if domain restriction is configured.
        
        Returns:
            True if domain restriction is active, False if all domains allowed
        """
        return bool(self.settings.allowed_email_domain_regex and 
                   self.settings.allowed_email_domain_regex != ".*")
