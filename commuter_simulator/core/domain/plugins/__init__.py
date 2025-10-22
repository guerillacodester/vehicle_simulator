"""
Spawning Plugins

Collection of passenger generation plugins for the commuter simulator.

Available Plugins:
- PoissonGeoJSONPlugin: Statistical spawning based on population data
- HistoricalReplayPlugin: Replay real-world passenger data

Usage:
    from commuter_simulator.core.domain.plugins import (
        PoissonGeoJSONPlugin,
        HistoricalReplayPlugin,
        PluginConfig,
        PluginType
    )
    
    # Create Poisson plugin
    poisson_config = PluginConfig(
        plugin_name="poisson",
        plugin_type=PluginType.STATISTICAL,
        country_code="BB"
    )
    poisson_plugin = PoissonGeoJSONPlugin(poisson_config, api_client)
    
    # Create historical replay plugin
    historical_config = PluginConfig(
        plugin_name="historical",
        plugin_type=PluginType.HISTORICAL,
        data_source="csv",
        custom_params={'csv_path': '/path/to/data.csv'}
    )
    historical_plugin = HistoricalReplayPlugin(historical_config, api_client)
"""

from commuter_simulator.core.domain.spawning_plugin import (
    BaseSpawningPlugin,
    PluginConfig,
    PluginType,
    PluginRegistry,
    SpawnContext,
    SpawnRequest
)

from commuter_simulator.core.domain.plugins.poisson_plugin import PoissonGeoJSONPlugin
from commuter_simulator.core.domain.plugins.historical_plugin import (
    HistoricalReplayPlugin,
    CSVExportHelper
)

__all__ = [
    # Base classes
    'BaseSpawningPlugin',
    'PluginConfig',
    'PluginType',
    'PluginRegistry',
    'SpawnContext',
    'SpawnRequest',
    
    # Plugin implementations
    'PoissonGeoJSONPlugin',
    'HistoricalReplayPlugin',
    
    # Helpers
    'CSVExportHelper'
]
