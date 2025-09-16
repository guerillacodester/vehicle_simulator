#!/usr/bin/env python3
"""
Telemetry Monitor and Analysis Script
====================================

Monitors GPS telemetry data from the vehicle simulator and analyzes:
1. Speed variations over time
2. Correlation between speed changes and road curvature
3. Heading changes indicating turns/corners
4. Physics behavior validation

Run this alongside the vehicle simulator to capture and analyze telemetry.
"""

import json
import time
import threading
from datetime import datetime, timezone
from typing import List, Dict, Tuple
import websocket
import math

# Try to import matplotlib with fallback
try:
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
    import matplotlib.pyplot as plt
    import numpy as np
    PLOTTING_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Plotting libraries not available ({e}). Analysis will continue without plots.")
    PLOTTING_AVAILABLE = False

class TelemetryMonitor:
    def __init__(self):
        self.telemetry_data = []
        self.ws = None
        self.monitoring = False
        self.start_time = None
        
    def on_message(self, ws, message):
        """Handle incoming telemetry messages"""
        try:
            data = json.loads(message)
            if isinstance(data, dict) and 'speed' in data:
                # Add timestamp for analysis
                timestamp = datetime.now(timezone.utc)
                if self.start_time is None:
                    self.start_time = timestamp
                
                # Calculate elapsed time
                elapsed = (timestamp - self.start_time).total_seconds()
                
                # Store telemetry with analysis fields
                record = {
                    'timestamp': timestamp.isoformat(),
                    'elapsed_seconds': elapsed,
                    'lat': data.get('lat', 0),
                    'lon': data.get('lon', 0),
                    'speed_kmh': data.get('speed', 0),
                    'heading': data.get('heading', 0),
                    'vehicle_reg': data.get('vehicleReg', ''),
                    'route': data.get('route', '')
                }
                
                self.telemetry_data.append(record)
                
                # Real-time logging
                print(f"⏱️  {elapsed:6.1f}s | 🚗 {record['speed_kmh']:5.1f} km/h | 🧭 {record['heading']:6.1f}° | 📍 {record['lat']:.6f}, {record['lon']:.6f}")
                
        except json.JSONDecodeError:
            pass  # Ignore non-JSON messages
        except Exception as e:
            print(f"Error processing message: {e}")
    
    def on_error(self, ws, error):
        print(f"WebSocket error: {error}")
    
    def on_close(self, ws, close_status_code, close_msg):
        print("📡 WebSocket connection closed")
        self.monitoring = False
    
    def on_open(self, ws):
        print("📡 Connected to GPS telemetry server")
        # Send device registration message
        auth_message = json.dumps({
            "type": "device_connect",
            "deviceId": "TELEMETRY-MONITOR",
            "token": "monitor-token"
        })
        ws.send(auth_message)
    
    def start_monitoring(self, duration_seconds=60):
        """Start monitoring telemetry for specified duration"""
        print(f"🔍 Starting telemetry monitoring for {duration_seconds} seconds...")
        print("📊 Real-time telemetry feed:")
        print("=" * 80)
        
        self.monitoring = True
        self.telemetry_data.clear()
        
        # Connect to GPS server WebSocket
        websocket.enableTrace(False)  # Disable debug output
        self.ws = websocket.WebSocketApp(
            "ws://localhost:5000/monitor",  # Monitor endpoint
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open
        )
        
        # Start WebSocket in background thread
        ws_thread = threading.Thread(target=self.ws.run_forever)
        ws_thread.daemon = True
        ws_thread.start()
        
        # Monitor for specified duration
        time.sleep(duration_seconds)
        
        # Stop monitoring
        self.monitoring = False
        if self.ws:
            self.ws.close()
        
        print("=" * 80)
        print(f"✅ Monitoring completed. Collected {len(self.telemetry_data)} data points.")
        
        return self.telemetry_data
    
    def calculate_curvature_indicators(self, data: List[Dict]) -> List[Dict]:
        """Calculate heading changes and curvature indicators"""
        if len(data) < 3:
            return data
        
        enhanced_data = []
        
        for i, record in enumerate(data):
            enhanced_record = record.copy()
            
            if i == 0:
                enhanced_record['heading_change'] = 0.0
                enhanced_record['curvature_indicator'] = 0.0
                enhanced_record['turn_type'] = 'STRAIGHT'
            else:
                # Calculate heading change from previous point
                prev_heading = data[i-1]['heading']
                current_heading = record['heading']
                
                # Handle heading wraparound (0° -> 360°)
                heading_diff = current_heading - prev_heading
                if heading_diff > 180:
                    heading_diff -= 360
                elif heading_diff < -180:
                    heading_diff += 360
                
                enhanced_record['heading_change'] = heading_diff
                
                # Calculate curvature indicator (rate of heading change)
                if i >= 2:
                    dt = record['elapsed_seconds'] - data[i-1]['elapsed_seconds']
                    if dt > 0:
                        curvature = abs(heading_diff) / dt  # degrees per second
                    else:
                        curvature = 0.0
                else:
                    curvature = abs(heading_diff)
                
                enhanced_record['curvature_indicator'] = curvature
                
                # Classify turn type
                abs_change = abs(heading_diff)
                if abs_change < 2:
                    enhanced_record['turn_type'] = 'STRAIGHT'
                elif abs_change < 10:
                    enhanced_record['turn_type'] = 'GENTLE'
                elif abs_change < 30:
                    enhanced_record['turn_type'] = 'MODERATE'
                else:
                    enhanced_record['turn_type'] = 'SHARP'
            
            enhanced_data.append(enhanced_record)
        
        return enhanced_data
    
    def analyze_speed_curvature_correlation(self, data: List[Dict]):
        """Analyze correlation between speed changes and road curvature"""
        print("\n🔬 SPEED-CURVATURE CORRELATION ANALYSIS")
        print("=" * 60)
        
        # Extract data arrays
        times = [d['elapsed_seconds'] for d in data]
        speeds = [d['speed_kmh'] for d in data]
        curvatures = [d['curvature_indicator'] for d in data]
        heading_changes = [d['heading_change'] for d in data]
        turn_types = [d['turn_type'] for d in data]
        
        # Speed statistics
        max_speed = max(speeds) if speeds else 0
        min_speed = min(speeds) if speeds else 0
        avg_speed = sum(speeds) / len(speeds) if speeds else 0
        
        print(f"📈 Speed Statistics:")
        print(f"   Max Speed: {max_speed:.1f} km/h")
        print(f"   Min Speed: {min_speed:.1f} km/h") 
        print(f"   Avg Speed: {avg_speed:.1f} km/h")
        print(f"   Speed Range: {max_speed - min_speed:.1f} km/h")
        
        # Turn analysis
        turn_counts = {}
        for turn_type in turn_types:
            turn_counts[turn_type] = turn_counts.get(turn_type, 0) + 1
        
        print(f"\n🔄 Turn Analysis:")
        for turn_type, count in sorted(turn_counts.items()):
            percentage = (count / len(data)) * 100
            print(f"   {turn_type:8}: {count:3d} points ({percentage:5.1f}%)")
        
        # Find speed drops during turns
        speed_drops = []
        for i in range(1, len(data)):
            curr = data[i]
            prev = data[i-1]
            
            speed_change = curr['speed_kmh'] - prev['speed_kmh']
            if speed_change < -5 and curr['curvature_indicator'] > 5:  # Speed drop > 5 km/h during turn
                speed_drops.append({
                    'time': curr['elapsed_seconds'],
                    'speed_drop': abs(speed_change),
                    'curvature': curr['curvature_indicator'],
                    'turn_type': curr['turn_type']
                })
        
        print(f"\n⬇️  Significant Speed Drops During Turns:")
        if speed_drops:
            for drop in speed_drops:
                print(f"   {drop['time']:6.1f}s: -{drop['speed_drop']:4.1f} km/h | {drop['turn_type']:8} turn | Curvature: {drop['curvature']:5.1f}°/s")
        else:
            print("   No significant speed drops detected during turns")
        
        return {
            'max_speed': max_speed,
            'min_speed': min_speed,
            'avg_speed': avg_speed,
            'turn_counts': turn_counts,
            'speed_drops': speed_drops
        }
    
    def create_telemetry_plots(self, data: List[Dict], analysis: Dict):
        """Create comprehensive telemetry visualization plots"""
        if not data:
            print("No data to plot")
            return
        
        if not PLOTTING_AVAILABLE:
            print("📊 Plotting libraries not available. Skipping visualization plots.")
            return
        
        print(f"\n📊 Creating telemetry visualization plots...")
        
        # Extract data for plotting
        times = [d['elapsed_seconds'] for d in data]
        speeds = [d['speed_kmh'] for d in data]
        headings = [d['heading'] for d in data]
        curvatures = [d['curvature_indicator'] for d in data]
        lats = [d['lat'] for d in data]
        lons = [d['lon'] for d in data]
        
        # Create comprehensive plot
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Vehicle Telemetry Analysis - Curvature-Aware Speed Control', fontsize=16, fontweight='bold')
        
        # Plot 1: Speed over time with curvature overlay
        ax1.plot(times, speeds, 'b-', linewidth=2, label='Speed (km/h)', alpha=0.8)
        ax1_twin = ax1.twinx()
        ax1_twin.plot(times, curvatures, 'r-', linewidth=1, alpha=0.6, label='Curvature (°/s)')
        ax1_twin.fill_between(times, curvatures, alpha=0.2, color='red')
        
        ax1.set_xlabel('Time (seconds)')
        ax1.set_ylabel('Speed (km/h)', color='blue')
        ax1_twin.set_ylabel('Curvature Indicator (°/s)', color='red')
        ax1.set_title('Speed vs Road Curvature')
        ax1.grid(True, alpha=0.3)
        ax1.legend(loc='upper left')
        ax1_twin.legend(loc='upper right')
        
        # Highlight speed drops during turns
        for drop in analysis['speed_drops']:
            ax1.axvline(x=drop['time'], color='orange', linestyle='--', alpha=0.7)
            ax1.annotate(f'-{drop["speed_drop"]:.1f}', 
                        xy=(drop['time'], speeds[int(drop['time']*2)]), 
                        xytext=(5, 5), textcoords='offset points',
                        fontsize=8, color='orange')
        
        # Plot 2: Heading changes over time
        ax2.plot(times, headings, 'g-', linewidth=2, alpha=0.8)
        ax2.set_xlabel('Time (seconds)')
        ax2.set_ylabel('Heading (degrees)')
        ax2.set_title('Vehicle Heading Changes')
        ax2.grid(True, alpha=0.3)
        ax2.set_ylim(0, 360)
        
        # Plot 3: GPS track (route path)
        ax3.plot(lons, lats, 'purple', linewidth=2, alpha=0.8)
        ax3.scatter(lons[0], lats[0], color='green', s=100, marker='o', label='Start', zorder=5)
        ax3.scatter(lons[-1], lats[-1], color='red', s=100, marker='s', label='End', zorder=5)
        
        # Color-code points by speed
        scatter = ax3.scatter(lons, lats, c=speeds, cmap='viridis', s=20, alpha=0.7, zorder=3)
        plt.colorbar(scatter, ax=ax3, label='Speed (km/h)')
        
        ax3.set_xlabel('Longitude')
        ax3.set_ylabel('Latitude')
        ax3.set_title('GPS Track (colored by speed)')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # Plot 4: Speed histogram with statistics
        ax4.hist(speeds, bins=20, alpha=0.7, color='skyblue', edgecolor='black')
        ax4.axvline(analysis['avg_speed'], color='red', linestyle='--', linewidth=2, label=f'Avg: {analysis["avg_speed"]:.1f} km/h')
        ax4.axvline(analysis['max_speed'], color='green', linestyle='--', linewidth=2, label=f'Max: {analysis["max_speed"]:.1f} km/h')
        ax4.axvline(analysis['min_speed'], color='orange', linestyle='--', linewidth=2, label=f'Min: {analysis["min_speed"]:.1f} km/h')
        
        ax4.set_xlabel('Speed (km/h)')
        ax4.set_ylabel('Frequency')
        ax4.set_title('Speed Distribution')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Save plot
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"telemetry_analysis_{timestamp}.png"
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"📊 Plot saved as: {filename}")
        
        # Show plot
        plt.show()

def main():
    """Main execution function"""
    print("🚗 Vehicle Telemetry Monitor & Analysis")
    print("=" * 50)
    print("This script will:")
    print("1. Monitor GPS telemetry for 60 seconds")
    print("2. Analyze speed changes vs road curvature")
    print("3. Create visualization plots")
    print()
    input("🔄 Start the vehicle simulator first, then press Enter to begin monitoring...")
    
    # Create monitor and start monitoring
    monitor = TelemetryMonitor()
    
    try:
        # Monitor for 60 seconds
        raw_data = monitor.start_monitoring(duration_seconds=60)
        
        if not raw_data:
            print("❌ No telemetry data collected. Ensure vehicle simulator is running.")
            return
        
        # Enhance data with curvature analysis
        enhanced_data = monitor.calculate_curvature_indicators(raw_data)
        
        # Analyze correlation between speed and curvature
        analysis = monitor.analyze_speed_curvature_correlation(enhanced_data)
        
        # Create plots
        monitor.create_telemetry_plots(enhanced_data, analysis)
        
        # Save data for future analysis
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        data_filename = f"telemetry_data_{timestamp}.json"
        with open(data_filename, 'w') as f:
            json.dump(enhanced_data, f, indent=2)
        print(f"💾 Raw data saved as: {data_filename}")
        
        print("\n✅ Analysis completed successfully!")
        
    except KeyboardInterrupt:
        print("\n⏹️  Monitoring interrupted by user")
    except Exception as e:
        print(f"❌ Error during monitoring: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()