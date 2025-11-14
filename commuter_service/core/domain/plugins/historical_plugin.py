"""
Historical Data Replay Plugin

Replays real-world passenger data from database or files.
Useful for validation, testing, and comparative analysis.

Data Sources:
- Database: Load from active_passengers or historical_passengers table
- CSV Files: Import from CSV exports
- API: Stream from external data source

Features:
- Replay at configurable speeds (1x, 2x, etc.)
- Date range filtering
- Preserve original timing and patterns
- Compare simulated vs actual behavior
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import csv
from pathlib import Path

from commuter_service.core.domain.spawning_plugin import (
    BaseSpawningPlugin,
    PluginConfig,
    PluginType,
    SpawnContext,
    SpawnRequest
)


class HistoricalReplayPlugin(BaseSpawningPlugin):
    """
    Replay historical passenger data.
    
    Configuration:
        config = PluginConfig(
            plugin_name="historical_replay",
            plugin_type=PluginType.HISTORICAL,
            data_source="database",  # or "csv" or "api"
            replay_speed=1.0,  # Real-time replay
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 1, 31),
            custom_params={
                'table_name': 'historical_passengers',
                'csv_path': '/path/to/data.csv'
            }
        )
    """
    
    def __init__(self, config: PluginConfig, api_client: Any, logger: Optional[logging.Logger] = None):
        super().__init__(config, api_client, logger)
        
        self.historical_data: List[Dict[str, Any]] = []
        self.current_index = 0
        self.replay_start_time: Optional[datetime] = None
        self.simulation_start_time: Optional[datetime] = None
    
    async def initialize(self) -> bool:
        """Load historical data from configured source"""
        try:
            self.logger.info(f"Initializing historical replay plugin from {self.config.data_source}...")
            
            if self.config.data_source == "database":
                await self._load_from_database()
            elif self.config.data_source == "csv":
                await self._load_from_csv()
            elif self.config.data_source == "api":
                await self._load_from_api()
            else:
                raise ValueError(f"Unknown data source: {self.config.data_source}")
            
            # Sort by spawn time
            self.historical_data.sort(key=lambda x: x['spawn_time'])
            
            if self.historical_data:
                self.replay_start_time = self.historical_data[0]['spawn_time']
                self.logger.info(
                    f"✅ Loaded {len(self.historical_data)} historical passengers "
                    f"from {self.replay_start_time}"
                )
            
            self._initialized = True
            return True
        
        except Exception as e:
            self.logger.error(f"❌ Failed to load historical data: {e}")
            return False
    
    async def _load_from_database(self):
        """Load from database table"""
        table_name = self.config.custom_params.get('table_name', 'historical_passengers')
        
        # Build query filters
        filters = {}
        if self.config.start_date:
            filters['spawn_time_gte'] = self.config.start_date.isoformat()
        if self.config.end_date:
            filters['spawn_time_lte'] = self.config.end_date.isoformat()
        
        # Query database (assuming API client has method for this)
        # This is a placeholder - actual implementation depends on API structure
        self.logger.info(f"Loading from database table: {table_name}")
        
        # Example API call (adapt to your API structure):
        # response = await self.api_client.query_table(table_name, filters)
        # self.historical_data = response['data']
        
        # For now, return empty list
        self.historical_data = []
        self.logger.warning("Database loading not yet implemented")
    
    async def _load_from_csv(self):
        """Load from CSV file"""
        csv_path = self.config.custom_params.get('csv_path')
        if not csv_path:
            raise ValueError("csv_path not specified in custom_params")
        
        path = Path(csv_path)
        if not path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        
        self.logger.info(f"Loading from CSV: {csv_path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                try:
                    # Parse CSV row into historical data format
                    spawn_time = datetime.fromisoformat(row['spawn_time'])
                    
                    # Apply date range filter
                    if self.config.start_date and spawn_time < self.config.start_date:
                        continue
                    if self.config.end_date and spawn_time > self.config.end_date:
                        continue
                    
                    record = {
                        'passenger_id': row['passenger_id'],
                        'spawn_time': spawn_time,
                        'spawn_location': (float(row['spawn_lat']), float(row['spawn_lon'])),
                        'destination': (float(row['dest_lat']), float(row['dest_lon'])),
                        'route_id': row['route_id'],
                        'actual_pickup_time': datetime.fromisoformat(row['pickup_time']) if row.get('pickup_time') else None,
                        'actual_dropoff_time': datetime.fromisoformat(row['dropoff_time']) if row.get('dropoff_time') else None,
                        'actual_wait_time_seconds': float(row['wait_time']) if row.get('wait_time') else None,
                        'zone_type': row.get('zone_type'),
                        'trip_purpose': row.get('trip_purpose')
                    }
                    
                    self.historical_data.append(record)
                
                except Exception as e:
                    self.logger.warning(f"Skipping invalid CSV row: {e}")
        
        self.logger.info(f"Loaded {len(self.historical_data)} records from CSV")
    
    async def _load_from_api(self):
        """Load from external API"""
        api_endpoint = self.config.custom_params.get('api_endpoint')
        if not api_endpoint:
            raise ValueError("api_endpoint not specified in custom_params")
        
        self.logger.info(f"Loading from API: {api_endpoint}")
        
        # Placeholder for API loading
        # Actual implementation depends on your API structure
        self.historical_data = []
        self.logger.warning("API loading not yet implemented")
    
    async def generate_spawn_requests(
        self,
        current_time: datetime,
        time_window_minutes: int,
        context: SpawnContext,
        **kwargs
    ) -> List[SpawnRequest]:
        """Generate spawn requests from historical data"""
        
        if not self._initialized or not self.historical_data:
            return []
        
        # Set simulation start time on first call
        if self.simulation_start_time is None:
            self.simulation_start_time = current_time
        
        # Calculate elapsed simulation time (with replay speed)
        elapsed_simulation = (current_time - self.simulation_start_time).total_seconds()
        elapsed_historical = elapsed_simulation * self.config.replay_speed
        
        # Calculate current historical time
        current_historical_time = self.replay_start_time + timedelta(seconds=elapsed_historical)
        window_end_time = current_historical_time + timedelta(minutes=time_window_minutes)
        
        # Find passengers that should spawn in this window
        spawn_requests = []
        
        while self.current_index < len(self.historical_data):
            record = self.historical_data[self.current_index]
            spawn_time = record['spawn_time']
            
            # Check if this spawn falls within the current window
            if spawn_time > window_end_time:
                break
            
            if spawn_time >= current_historical_time:
                # Create spawn request from historical data
                request = SpawnRequest(
                    passenger_id=record['passenger_id'],
                    spawn_location=record['spawn_location'],
                    destination_location=record['destination'],
                    route_id=record['route_id'],
                    spawn_time=current_time,  # Use current simulation time
                    spawn_context=context,
                    zone_type=record.get('zone_type'),
                    trip_purpose=record.get('trip_purpose'),
                    generation_method='historical_replay',
                    is_historical=True,
                    actual_pickup_time=record.get('actual_pickup_time'),
                    actual_dropoff_time=record.get('actual_dropoff_time'),
                    actual_wait_time_seconds=record.get('actual_wait_time_seconds'),
                    plugin_name=self.config.plugin_name,
                    plugin_version='1.0.0'
                )
                
                spawn_requests.append(request)
            
            self.current_index += 1
        
        if spawn_requests:
            self._record_spawns(spawn_requests)
            self.logger.info(
                f"Replayed {len(spawn_requests)} historical passengers "
                f"(historical time: {current_historical_time.isoformat()}, "
                f"speed: {self.config.replay_speed}x)"
            )
        
        # Check if we've reached the end
        if self.current_index >= len(self.historical_data):
            self.logger.info("✅ Historical replay complete")
        
        return spawn_requests
    
    async def shutdown(self):
        """Cleanup plugin resources"""
        self.logger.info(f"Shutting down historical replay plugin ({len(self.historical_data)} records processed)")
        self.historical_data = []
        self.current_index = 0
        self._initialized = False
    
    def reset_replay(self):
        """Reset replay to beginning"""
        self.current_index = 0
        self.simulation_start_time = None
        self.logger.info("Historical replay reset to beginning")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get plugin statistics"""
        stats = super().get_stats()
        stats.update({
            'total_records': len(self.historical_data),
            'current_index': self.current_index,
            'records_remaining': len(self.historical_data) - self.current_index,
            'replay_speed': self.config.replay_speed,
            'replay_complete': self.current_index >= len(self.historical_data)
        })
        return stats


class CSVExportHelper:
    """
    Helper class for exporting simulated data to CSV for later replay.
    
    Usage:
        exporter = CSVExportHelper('/path/to/output.csv')
        
        # During simulation, record spawns
        exporter.record_spawn(spawn_request, pickup_time, dropoff_time, wait_time)
        
        # At end, close file
        exporter.close()
    """
    
    def __init__(self, csv_path: str):
        self.csv_path = Path(csv_path)
        self.file = None
        self.writer = None
        self._initialize_file()
    
    def _initialize_file(self):
        """Initialize CSV file with headers"""
        self.file = open(self.csv_path, 'w', newline='', encoding='utf-8')
        
        fieldnames = [
            'passenger_id', 'spawn_time', 'spawn_lat', 'spawn_lon',
            'dest_lat', 'dest_lon', 'route_id', 'pickup_time',
            'dropoff_time', 'wait_time', 'zone_type', 'trip_purpose'
        ]
        
        self.writer = csv.DictWriter(self.file, fieldnames=fieldnames)
        self.writer.writeheader()
    
    def record_spawn(
        self,
        spawn_request: SpawnRequest,
        pickup_time: Optional[datetime] = None,
        dropoff_time: Optional[datetime] = None,
        wait_time_seconds: Optional[float] = None
    ):
        """Record a spawn event"""
        row = {
            'passenger_id': spawn_request.passenger_id or 'generated',
            'spawn_time': spawn_request.spawn_time.isoformat(),
            'spawn_lat': spawn_request.spawn_location[0],
            'spawn_lon': spawn_request.spawn_location[1],
            'dest_lat': spawn_request.destination_location[0],
            'dest_lon': spawn_request.destination_location[1],
            'route_id': spawn_request.route_id,
            'pickup_time': pickup_time.isoformat() if pickup_time else '',
            'dropoff_time': dropoff_time.isoformat() if dropoff_time else '',
            'wait_time': wait_time_seconds or '',
            'zone_type': spawn_request.zone_type or '',
            'trip_purpose': spawn_request.trip_purpose or ''
        }
        
        self.writer.writerow(row)
    
    def close(self):
        """Close CSV file"""
        if self.file:
            self.file.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
