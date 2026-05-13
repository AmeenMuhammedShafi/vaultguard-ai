"""
Face Recognition Core Module
Provides authentication and access control functionality
"""

from .access_control import DualPersonAccessControl
from .authentication_terminal import AuthenticationTerminal

__all__ = ['DualPersonAccessControl', 'AuthenticationTerminal']
