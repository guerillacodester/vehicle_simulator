"""Compatibility shim: re-export the existing launcher API surface so we can migrate to
`arknet_transit_launcher` implementations incrementally.

This module currently imports from the legacy `launcher` package and re-exports the
same names. In future it can be replaced with native implementations under
`arknet_transit_launcher` to move runtime to the new package.
"""

# Re-export selected symbols from the existing `launcher` package
try:
    from launcher.service_manager import app, manager, ManagedService, configure_cors
    from launcher.config import ConfigurationManager
    from launcher.socket_server import sio, socket_app
except Exception:
    # If legacy launcher package isn't available, expose placeholders to fail loud
    app = None
    manager = None
    ManagedService = None
    configure_cors = None
    ConfigurationManager = None
    sio = None
    socket_app = None

__all__ = [
    "app",
    "manager",
    "ManagedService",
    "configure_cors",
    "ConfigurationManager",
    "sio",
    "socket_app",
]
