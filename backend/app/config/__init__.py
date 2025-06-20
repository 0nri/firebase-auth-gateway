"""Configuration package for Auth Gateway."""

from .settings import Settings, get_settings, setup_logging

__all__ = ["Settings", "get_settings", "setup_logging"]
