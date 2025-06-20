"""
Tests for DomainService.
"""
import pytest
from unittest.mock import patch, Mock
from fastapi import HTTPException

from app.services.domain_service import DomainService


class TestDomainService:
    """Test cases for DomainService."""
    
    def test_init_with_valid_regex(self, test_settings):
        """Test DomainService initialization with valid regex."""
        service = DomainService(test_settings)
        assert service.settings == test_settings
        assert service._compiled_regex is not None
    
    def test_init_with_invalid_regex(self, test_settings):
        """Test DomainService initialization with invalid regex."""
        test_settings.allowed_email_domain_regex = "[invalid regex"
        
        service = DomainService(test_settings)
        
        # Should fall back to allow-all regex
        assert service._compiled_regex is not None
        # Should allow all emails when regex is invalid
        assert service.validate_email_domain("test@anydomain.com") is True
    
    def test_validate_email_domain_valid(self, test_settings):
        """Test email domain validation with valid domain."""
        service = DomainService(test_settings)
        
        result = service.validate_email_domain("user@example.com")
        
        assert result is True
    
    def test_validate_email_domain_invalid(self, test_settings):
        """Test email domain validation with invalid domain."""
        service = DomainService(test_settings)
        
        result = service.validate_email_domain("user@invalid.org")
        
        assert result is False
    
    def test_validate_email_domain_empty_email(self, test_settings):
        """Test email domain validation with empty email."""
        service = DomainService(test_settings)
        
        result = service.validate_email_domain("")
        
        assert result is False
    
    def test_validate_email_domain_none_email(self, test_settings):
        """Test email domain validation with None email."""
        service = DomainService(test_settings)
        
        result = service.validate_email_domain(None)
        
        assert result is False
    
    def test_validate_email_domain_allow_all_regex(self, test_settings):
        """Test email domain validation with allow-all regex."""
        test_settings.allowed_email_domain_regex = ".*"
        service = DomainService(test_settings)
        
        result = service.validate_email_domain("user@anydomain.com")
        
        assert result is True
    
    def test_validate_email_domain_no_regex(self, test_settings):
        """Test email domain validation with no regex configured."""
        test_settings.allowed_email_domain_regex = ""
        service = DomainService(test_settings)
        
        result = service.validate_email_domain("user@anydomain.com")
        
        assert result is True
    
    def test_validate_email_domain_regex_error(self, test_settings):
        """Test email domain validation when regex matching fails."""
        service = DomainService(test_settings)
        
        # Mock the compiled regex to raise an exception when match is called
        mock_regex = Mock()
        mock_regex.match.side_effect = Exception("Regex error")
        service._compiled_regex = mock_regex
        
        result = service.validate_email_domain("user@example.com")
        
        # Should be permissive on error
        assert result is True
    
    def test_validate_and_raise_success(self, test_settings):
        """Test validate_and_raise with valid email."""
        service = DomainService(test_settings)
        
        # Should not raise any exception
        service.validate_and_raise("user@example.com")
    
    def test_validate_and_raise_empty_email(self, test_settings):
        """Test validate_and_raise with empty email."""
        service = DomainService(test_settings)
        
        with pytest.raises(HTTPException) as exc:
            service.validate_and_raise("")
        
        assert exc.value.status_code == 400
        assert "Email address is required" in exc.value.detail
    
    def test_validate_and_raise_invalid_domain(self, test_settings):
        """Test validate_and_raise with invalid domain."""
        service = DomainService(test_settings)
        
        with pytest.raises(HTTPException) as exc:
            service.validate_and_raise("user@invalid.org")
        
        assert exc.value.status_code == 403
        assert "Email domain not allowed" in exc.value.detail
    
    def test_get_domain_from_email_success(self, test_settings):
        """Test domain extraction from valid email."""
        service = DomainService(test_settings)
        
        domain = service.get_domain_from_email("user@example.com")
        
        assert domain == "example.com"
    
    def test_get_domain_from_email_uppercase(self, test_settings):
        """Test domain extraction with uppercase domain."""
        service = DomainService(test_settings)
        
        domain = service.get_domain_from_email("user@EXAMPLE.COM")
        
        assert domain == "example.com"
    
    def test_get_domain_from_email_subdomain(self, test_settings):
        """Test domain extraction with subdomain."""
        service = DomainService(test_settings)
        
        domain = service.get_domain_from_email("user@mail.example.com")
        
        assert domain == "mail.example.com"
    
    def test_get_domain_from_email_no_at_symbol(self, test_settings):
        """Test domain extraction from email without @ symbol."""
        service = DomainService(test_settings)
        
        domain = service.get_domain_from_email("invalid-email")
        
        assert domain == ""
    
    def test_get_domain_from_email_empty(self, test_settings):
        """Test domain extraction from empty email."""
        service = DomainService(test_settings)
        
        domain = service.get_domain_from_email("")
        
        assert domain == ""
    
    def test_get_domain_from_email_multiple_at(self, test_settings):
        """Test domain extraction from email with multiple @ symbols."""
        service = DomainService(test_settings)
        
        domain = service.get_domain_from_email("user@domain@example.com")
        
        # Should return the last part after @
        assert domain == "example.com"
    
    def test_is_domain_configured_true(self, test_settings):
        """Test is_domain_configured when domain restriction is active."""
        service = DomainService(test_settings)
        
        result = service.is_domain_configured()
        
        assert result is True
    
    def test_is_domain_configured_false_allow_all(self, test_settings):
        """Test is_domain_configured when allow-all regex is used."""
        test_settings.allowed_email_domain_regex = ".*"
        service = DomainService(test_settings)
        
        result = service.is_domain_configured()
        
        assert result is False
    
    def test_is_domain_configured_false_empty(self, test_settings):
        """Test is_domain_configured when no regex is configured."""
        test_settings.allowed_email_domain_regex = ""
        service = DomainService(test_settings)
        
        result = service.is_domain_configured()
        
        assert result is False
    
    def test_complex_domain_regex(self, test_settings):
        """Test complex domain regex patterns."""
        # Allow multiple specific domains
        test_settings.allowed_email_domain_regex = r".*@(example\.com|test\.org|subdomain\.example\.com)$"
        service = DomainService(test_settings)
        
        # Valid domains
        assert service.validate_email_domain("user@example.com") is True
        assert service.validate_email_domain("user@test.org") is True
        assert service.validate_email_domain("user@subdomain.example.com") is True
        
        # Invalid domains
        assert service.validate_email_domain("user@invalid.com") is False
        assert service.validate_email_domain("user@example.org") is False
    
    def test_case_sensitive_domain_regex(self, test_settings):
        """Test case-sensitive domain regex patterns."""
        # Case-sensitive regex
        test_settings.allowed_email_domain_regex = r".*@Example\.com$"
        service = DomainService(test_settings)
        
        # Should match case exactly
        assert service.validate_email_domain("user@Example.com") is True
        assert service.validate_email_domain("user@example.com") is False
        assert service.validate_email_domain("user@EXAMPLE.COM") is False
