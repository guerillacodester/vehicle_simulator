"""
Spawning Services

Complete passenger spawning subsystem with plugin architecture.

Components:
- SpawningCoordinator: Background task manager for automatic spawning
- MultiContextCoordinator: Manages multiple spawning contexts
- GeoJSONDataLoader: Loads population and amenity data
- PopulationZone: Data structure for geographic zones

Usage:
    from commuter_simulator.services.spawning import (
        SpawningCoordinator,
        MultiContextCoordinator,
        GeoJSONDataLoader,
        PopulationZone
    )
    
    # Load geographic data
    loader = GeoJSONDataLoader(api_client)
    await loader.load_geojson_data("BB")
    
    # Setup plugin and coordinator
    plugin = PoissonGeoJSONPlugin(config, api_client)
    registry = PluginRegistry(api_client)
    registry.register_plugin(plugin)
    await registry.initialize_all()
    
    # Start spawning coordinator
    coordinator = SpawningCoordinator(
        plugin_registry=registry,
        spawn_interval=30.0,
        on_spawn_callback=handle_spawn
    )
    await coordinator.start()
"""

from commuter_simulator.services.spawning.coordinator import (
    SpawningCoordinator,
    MultiContextCoordinator
)

from commuter_simulator.services.spawning.geojson_loader import (
    GeoJSONDataLoader,
    PopulationZone
)

__all__ = [
    'SpawningCoordinator',
    'MultiContextCoordinator',
    'GeoJSONDataLoader',
    'PopulationZone'
]
