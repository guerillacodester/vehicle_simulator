#!/usr/bin/env python3
"""
Vehicle Simulator Logging System
---------------------------------
Centralized logging system with separation of concerns.
Provides DEBUG, INFO, WARNING, ERROR levels with configurable output.
Supports console, file, and structured logging for different components.
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
import json


class LogLevel(Enum):
    """Standard logging levels with verbose mode support."""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class LogComponent(Enum):
    """Vehicle simulator components for targeted logging."""
    MAIN = "main"
    DEPOT = "depot"
    VEHICLE = "vehicle"
    GPS = "gps"
    ENGINE = "engine"
    NAVIGATION = "navigation"
    TELEMETRY = "telemetry"
    API = "api"
    DATABASE = "database"
    SIMULATOR = "simulator"
    FLEET = "fleet"
    DISPATCHER = "dispatcher"


class LoggingMode(Enum):
    """Logging output modes for different verbosity levels."""
    NORMAL = "normal"      # Basic INFO messages only
    DEBUG = "debug"        # Clean debug status messages
    VERBOSE = "verbose"    # Full detailed output


class VehicleSimulatorLogger:
    """
    Centralized logging system for vehicle simulator.
    Follows separation of concerns by providing component-specific loggers.
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        """Singleton pattern for centralized logging configuration."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize logging system if not already done."""
        if not self._initialized:
            self._setup_logging_system()
            VehicleSimulatorLogger._initialized = True
    
    def _setup_logging_system(self):
        """Setup the core logging infrastructure."""
        # Configuration
        self.log_level = LogLevel.INFO
        self.logging_mode = LoggingMode.NORMAL
        self.verbose_mode = False  # Legacy compatibility
        self.console_enabled = True
        self.file_enabled = True
        self.structured_logging = False
        
        # Paths
        self.log_directory = "logs"
        self.log_file = "vehicle_simulator.log"
        self.error_log_file = "vehicle_simulator_errors.log"
        
        # Component loggers cache
        self._component_loggers: Dict[str, logging.Logger] = {}
        
        # Create log directory
        self._ensure_log_directory()
        
        # Setup root logger for vehicle simulator
        self._setup_root_logger()
        
        # Setup formatters
        self._setup_formatters()
    
    def _ensure_log_directory(self):
        """Create logs directory if it doesn't exist."""
        if self.file_enabled:
            os.makedirs(self.log_directory, exist_ok=True)
    
    def _setup_root_logger(self):
        """Configure the root logger for vehicle simulator."""
        # Get root logger for our namespace
        self.root_logger = logging.getLogger('world.vehicle_simulator')
        self.root_logger.setLevel(logging.DEBUG)  # Capture everything, filter at handler level
        
        # Clear any existing handlers
        self.root_logger.handlers.clear()
        
        # Prevent propagation to avoid duplicate messages
        self.root_logger.propagate = False
    
    def _setup_formatters(self):
        """Setup different formatters for different output types."""
        # Console formatter - normal mode (clean)
        self.console_normal_formatter = logging.Formatter(
            '%(asctime)s | %(message)s',
            datefmt='%H:%M:%S'
        )
        
        # Console formatter - debug mode (status-focused)
        self.console_debug_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-5s | %(message)s',
            datefmt='%H:%M:%S'
        )
        
        # Console formatter - verbose mode (detailed)
        self.console_verbose_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%H:%M:%S'
        )
        
        # File formatter (always detailed)
        self.file_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(funcName)s() | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Structured formatter (JSON for analysis)
        self.structured_formatter = self._create_json_formatter()
    
    def _create_json_formatter(self):
        """Create JSON formatter for structured logging."""
        class JSONFormatter(logging.Formatter):
            def format(self, record):
                log_entry = {
                    'timestamp': datetime.fromtimestamp(record.created).isoformat(),
                    'level': record.levelname,
                    'component': record.name.split('.')[-1] if '.' in record.name else record.name,
                    'module': record.module,
                    'function': record.funcName,
                    'line': record.lineno,
                    'message': record.getMessage(),
                }
                
                # Add exception info if present
                if record.exc_info:
                    log_entry['exception'] = self.formatException(record.exc_info)
                
                return json.dumps(log_entry)
        
        return JSONFormatter()
    
    def _create_normal_mode_filter(self):
        """Create a filter for normal mode that only shows essential messages."""
        class NormalModeFilter(logging.Filter):
            def filter(self, record):
                # Always show ERROR and WARNING levels regardless of content
                if record.levelno >= logging.WARNING:
                    return True
                
                message = record.getMessage()
                
                # Whitelist only essential high-level messages
                essential_messages = [
                    # Core lifecycle events
                    "🚌 Vehicle Simulator Starting...",
                    "🚌 Starting Basic Vehicle Simulator",
                    "✅ Basic Vehicle Simulator started",
                    "🛑 Stopping simulation...",
                    "✅ Simulation stopped",
                    "Vehicle Simulator stopped",
                    "Timed Simulation Complete",
                    
                    # Key status displays
                    "🚌 Vehicle Simulator - Timed Mode",
                    "⏱️  Update Interval:",
                    "⏰ Duration:",
                    "🚀 Mode:",
                    "📡 GPS transmission:",
                    "🚌 Vehicle simulation started",
                    
                    # Dashboard separators
                    "============================================================",
                    "------------------------------------------------------------",
                    
                    # High-level system status
                    "🎭 Created",
                    "dummy vehicles"
                ]
                
                # Check for exact essential messages or key patterns
                for essential in essential_messages:
                    if essential in message:
                        return True
                
                # Allow fallback messages
                if "Falling back to basic vehicle simulator" in message:
                    return True
                
                # Allow GPS device status (the emoji lines)
                if message.strip().startswith("📡") and ("GPS device" in message):
                    return True
                
                # Block everything else in normal mode
                return False
        
        return NormalModeFilter()
    
    def configure(self, 
                  level: LogLevel = LogLevel.INFO,
                  verbose: bool = False,
                  console: bool = True,
                  file_logging: bool = True,
                  structured: bool = False,
                  log_dir: str = "logs"):
        """
        Configure the logging system.
        
        Args:
            level: Minimum log level to capture
            verbose: Enable verbose/debug mode
            console: Enable console output
            file_logging: Enable file output
            structured: Enable JSON structured logging
            log_dir: Directory for log files
        """
        self.log_level = LogLevel.DEBUG if verbose else level
        self.verbose_mode = verbose
        self.console_enabled = console
        self.file_enabled = file_logging
        self.structured_logging = structured
        self.log_directory = log_dir
        
        # Recreate handlers with new configuration
        self._recreate_handlers()
        
        # Log configuration change
        config_logger = self.get_logger(LogComponent.MAIN)
        config_logger.info(f"Logging system configured: level={level.name}, verbose={verbose}, "
                          f"console={console}, file={file_logging}, structured={structured}")
    
    def _recreate_handlers(self):
        """Recreate all handlers with current configuration."""
        # Clear existing handlers
        self.root_logger.handlers.clear()
        
        # Ensure log directory exists
        self._ensure_log_directory()
        
        # Console handler with appropriate formatter and filtering
        if self.console_enabled:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(self.log_level.value)
            
            # Choose formatter based on logging mode
            if self.logging_mode == LoggingMode.VERBOSE:
                console_handler.setFormatter(self.console_verbose_formatter)
            elif self.logging_mode == LoggingMode.DEBUG:
                console_handler.setFormatter(self.console_debug_formatter)
            else:  # NORMAL mode - very selective filtering
                console_handler.setFormatter(self.console_normal_formatter)
                console_handler.addFilter(self._create_normal_mode_filter())
                
            self.root_logger.addHandler(console_handler)
        
        # File handler with UTF-8 encoding
        if self.file_enabled:
            file_handler = logging.handlers.RotatingFileHandler(
                os.path.join(self.log_directory, self.log_file),
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5,
                encoding='utf-8'
            )
            file_handler.setLevel(logging.DEBUG)  # File captures everything
            formatter = self.structured_formatter if self.structured_logging else self.file_formatter
            file_handler.setFormatter(formatter)
            self.root_logger.addHandler(file_handler)
            
            # Separate error log with UTF-8 encoding
            error_handler = logging.handlers.RotatingFileHandler(
                os.path.join(self.log_directory, self.error_log_file),
                maxBytes=5*1024*1024,  # 5MB
                backupCount=3,
                encoding='utf-8'
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(self.file_formatter)
            self.root_logger.addHandler(error_handler)
    
    def get_logger(self, component: LogComponent) -> logging.Logger:
        """
        Get a logger for a specific component.
        
        Args:
            component: The simulator component requesting the logger
            
        Returns:
            Configured logger for the component
        """
        component_name = component.value
        logger_name = f"world.vehicle_simulator.{component_name}"
        
        if logger_name not in self._component_loggers:
            logger = logging.getLogger(logger_name)
            logger.setLevel(logging.DEBUG)  # Let handlers control filtering
            self._component_loggers[logger_name] = logger
        
        return self._component_loggers[logger_name]
    
    def get_child_logger(self, component: LogComponent, child_name: str) -> logging.Logger:
        """
        Get a child logger for a specific sub-component.
        
        Args:
            component: Parent component
            child_name: Name of the child component
            
        Returns:
            Configured child logger
        """
        parent_logger = self.get_logger(component)
        return parent_logger.getChild(child_name)
    
    def set_level(self, level: LogLevel):
        """Change the logging level dynamically."""
        self.log_level = level
        for handler in self.root_logger.handlers:
            if isinstance(handler, logging.StreamHandler) and handler.stream == sys.stdout:
                handler.setLevel(level.value)
    
    def set_logging_mode(self, mode: LoggingMode):
        """Set the logging output mode."""
        self.logging_mode = mode
        
        # Set appropriate log levels
        if mode == LoggingMode.VERBOSE:
            self.log_level = LogLevel.DEBUG
            self.verbose_mode = True
        elif mode == LoggingMode.DEBUG:
            self.log_level = LogLevel.DEBUG
            self.verbose_mode = False
        else:  # NORMAL
            self.log_level = LogLevel.INFO
            self.verbose_mode = False
        
        # Recreate handlers with new formatting
        self._recreate_handlers()
    
    def enable_verbose(self):
        """Enable verbose/debug mode."""
        self.set_logging_mode(LoggingMode.VERBOSE)
    
    def disable_verbose(self):
        """Disable verbose/debug mode."""
        self.set_logging_mode(LoggingMode.DEBUG if self.log_level == LogLevel.DEBUG else LoggingMode.NORMAL)
    
    def log_system_info(self):
        """Log system configuration and status."""
        main_logger = self.get_logger(LogComponent.MAIN)
        
        # Only show detailed info in debug/verbose modes
        if self.logging_mode == LoggingMode.NORMAL:
            main_logger.info("🚌 Vehicle Simulator Starting...")
        else:
            main_logger.info("=" * 60)
            main_logger.info("VEHICLE SIMULATOR LOGGING SYSTEM")
            main_logger.info("=" * 60)
            main_logger.info(f"Log Level: {self.log_level.name}")
            main_logger.info(f"Logging Mode: {self.logging_mode.value}")
            main_logger.info(f"Console Logging: {self.console_enabled}")
            main_logger.info(f"File Logging: {self.file_enabled}")
            main_logger.info(f"Structured Logging: {self.structured_logging}")
            if self.file_enabled:
                main_logger.info(f"Log Directory: {os.path.abspath(self.log_directory)}")
            main_logger.info("=" * 60)


# Convenience functions for easy access
_logger_system = None

def get_logging_system() -> VehicleSimulatorLogger:
    """Get the singleton logging system instance."""
    global _logger_system
    if _logger_system is None:
        _logger_system = VehicleSimulatorLogger()
    return _logger_system

def get_logger(component: LogComponent) -> logging.Logger:
    """Convenience function to get a component logger."""
    return get_logging_system().get_logger(component)

def configure_logging(level: LogLevel = LogLevel.INFO,
                     verbose: bool = False,
                     console: bool = True,
                     file_logging: bool = True,
                     structured: bool = False,
                     log_dir: str = "logs"):
    """Convenience function to configure logging."""
    return get_logging_system().configure(level, verbose, console, file_logging, structured, log_dir)


# Example usage for different components
if __name__ == "__main__":
    # Configure logging
    configure_logging(verbose=True)
    
    # Get component loggers
    main_logger = get_logger(LogComponent.MAIN)
    gps_logger = get_logger(LogComponent.GPS)
    engine_logger = get_logger(LogComponent.ENGINE)
    
    # Log system info
    get_logging_system().log_system_info()
    
    # Example logging
    main_logger.info("Vehicle simulator starting up")
    gps_logger.debug("GPS device initialized")
    engine_logger.warning("Engine temperature high")
    
    try:
        raise ValueError("Test exception")
    except Exception as e:
        main_logger.error("Test error occurred", exc_info=True)