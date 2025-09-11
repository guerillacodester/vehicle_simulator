#!/usr/bin/env python3
"""
Vehicle Simulator Logging System Demo
-------------------------------------
Demonstrates how to use the new centralized logging system.
"""

import os
import sys
from pathlib import Path

# Add the project to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(current_dir.parent.parent))

from world.vehicle_simulator.utils.logging_system import (
    get_logger, configure_logging, LogLevel, LogComponent, get_logging_system
)


def demo_basic_logging():
    """Demonstrate basic logging functionality."""
    
    # Configure logging system
    configure_logging(
        level=LogLevel.DEBUG,
        verbose=True,
        console=True,
        file_logging=True,
        log_dir="demo_logs"
    )
    
    # Get loggers for different components
    main_logger = get_logger(LogComponent.MAIN)
    gps_logger = get_logger(LogComponent.GPS)
    engine_logger = get_logger(LogComponent.ENGINE)
    vehicle_logger = get_logger(LogComponent.VEHICLE)
    
    # Log system initialization
    get_logging_system().log_system_info()
    
    # Demonstrate different log levels
    main_logger.debug("🔧 Debug message - system initialization details")
    main_logger.info("ℹ️ Info message - normal operation status")
    main_logger.warning("⚠️ Warning message - something needs attention")
    main_logger.error("❌ Error message - something failed")
    
    # Demonstrate component-specific logging
    gps_logger.info("📡 GPS device initialized")
    gps_logger.debug("📍 GPS coordinates updated: lat=13.1, lon=-59.6")
    gps_logger.warning("⚠️ GPS signal weak")
    
    engine_logger.info("🚗 Engine starting up")
    engine_logger.debug("🔧 Engine RPM: 1500")
    engine_logger.warning("🌡️ Engine temperature high: 95°C")
    
    vehicle_logger.info("🚌 Vehicle ZR1001 active")
    vehicle_logger.debug("📊 Vehicle status: speed=45km/h, passengers=8")
    
    # Demonstrate child loggers
    telemetry_logger = get_logging_system().get_child_logger(LogComponent.GPS, "telemetry")
    telemetry_logger.info("📊 Telemetry data transmitted")
    
    # Demonstrate exception logging
    try:
        raise ValueError("Simulated error for demo")
    except Exception as e:
        main_logger.error("Exception occurred during demo", exc_info=True)
    
    print("\n" + "="*60)
    print("🎯 LOGGING DEMO COMPLETE")
    print("="*60)
    print("📁 Check the 'demo_logs' directory for log files")
    print("📋 Log files created:")
    print("   - vehicle_simulator.log (all messages)")
    print("   - vehicle_simulator_errors.log (errors only)")
    print("🔧 Use --verbose flag for DEBUG level logging")
    print("⚙️ Configure logging in config.ini for production")


def demo_configuration_modes():
    """Demonstrate different logging configurations."""
    
    print("\n" + "="*60)
    print("🔧 LOGGING CONFIGURATION MODES")
    print("="*60)
    
    # 1. Console only (for development)
    print("\n1️⃣ Console-only logging (development mode)")
    configure_logging(
        level=LogLevel.INFO,
        console=True,
        file_logging=False
    )
    
    logger = get_logger(LogComponent.MAIN)
    logger.info("Development mode: console output only")
    
    # 2. File only (for production)
    print("\n2️⃣ File-only logging (production mode)")
    configure_logging(
        level=LogLevel.WARNING,
        console=False,
        file_logging=True,
        log_dir="prod_logs"
    )
    
    logger = get_logger(LogComponent.MAIN)
    logger.warning("Production mode: file output only (this won't show in console)")
    print("   (Warning logged to file only)")
    
    # 3. Structured logging (for analysis)
    print("\n3️⃣ Structured JSON logging (analysis mode)")
    configure_logging(
        level=LogLevel.INFO,
        console=False,
        file_logging=True,
        structured=True,
        log_dir="json_logs"
    )
    
    logger = get_logger(LogComponent.MAIN)
    logger.info("JSON structured logging for automated analysis")
    print("   (JSON format logged to file)")
    
    # 4. Verbose debug mode
    print("\n4️⃣ Verbose debug mode")
    configure_logging(
        level=LogLevel.DEBUG,
        verbose=True,
        console=True,
        file_logging=True
    )
    
    logger = get_logger(LogComponent.MAIN)
    logger.debug("Verbose mode: maximum detail logging")


def demo_component_filtering():
    """Demonstrate component-specific log filtering."""
    
    print("\n" + "="*60)
    print("🎯 COMPONENT-SPECIFIC FILTERING")
    print("="*60)
    
    # Configure with INFO level
    configure_logging(level=LogLevel.INFO, console=True, file_logging=False)
    
    # Get different component loggers
    components = [
        (LogComponent.GPS, "GPS system"),
        (LogComponent.ENGINE, "Engine system"),
        (LogComponent.NAVIGATION, "Navigation system"),
        (LogComponent.TELEMETRY, "Telemetry system")
    ]
    
    print("\nComponent logging demonstration:")
    for component, description in components:
        logger = get_logger(component)
        logger.info(f"✅ {description} operational")
        logger.debug(f"🔧 {description} debug info (filtered out at INFO level)")
    
    print("\n💡 Tip: Set component-specific levels in config.ini")
    print("   Example: gps=DEBUG, engine=WARNING")


if __name__ == "__main__":
    print("🚀 Vehicle Simulator Logging System Demo")
    print("="*60)
    
    try:
        demo_basic_logging()
        demo_configuration_modes()
        demo_component_filtering()
        
    except KeyboardInterrupt:
        print("\n⏹️ Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n🎉 Demo complete! Check the log directories for output files.")