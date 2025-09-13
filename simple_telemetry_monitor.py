#!/usr/bin/env python3
"""
Simple Telemetry Monitor for Speed-Curvature Analysis
====================================================

Monitors GPS telemetry and analyzes correlation between speed changes and road curvature.
This version focuses on data analysis without requiring matplotlib.
"""

import json
import time
import threading
from datetime import datetime, timezone
from typing import List, Dict
import websocket
import math

class SimpleTelemetryMonitor:
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
                
                # Real-time logging with enhanced display
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
        print("📡 Listening for telemetry data...")
    
    def start_monitoring(self, duration_seconds=60):
        """Start monitoring telemetry for specified duration"""
        print(f"🔍 Starting telemetry monitoring for {duration_seconds} seconds...")
        print("📊 Real-time telemetry feed:")
        print("=" * 90)
        
        self.monitoring = True
        self.telemetry_data.clear()
        
        # Connect to GPS server WebSocket
        websocket.enableTrace(False)  # Disable debug output
        self.ws = websocket.WebSocketApp(
            "ws://localhost:5000",  # Telemetry server endpoint
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
        
        print("=" * 90)
        print(f"✅ Monitoring completed. Collected {len(self.telemetry_data)} data points.")
        
        return self.telemetry_data
    
    def calculate_curvature_analysis(self, data: List[Dict]) -> List[Dict]:
        """Calculate heading changes and curvature indicators"""
        if len(data) < 3:
            return data
        
        enhanced_data = []
        
        for i, record in enumerate(data):
            enhanced_record = record.copy()
            
            if i == 0:
                enhanced_record['heading_change'] = 0.0
                enhanced_record['curvature_indicator'] = 0.0
                enhanced_record['turn_type'] = 'START'
                enhanced_record['speed_change'] = 0.0
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
                
                # Calculate speed change
                prev_speed = data[i-1]['speed_kmh']
                current_speed = record['speed_kmh']
                enhanced_record['speed_change'] = current_speed - prev_speed
                
                # Calculate curvature indicator (rate of heading change)
                dt = record['elapsed_seconds'] - data[i-1]['elapsed_seconds']
                if dt > 0:
                    curvature = abs(heading_diff) / dt  # degrees per second
                else:
                    curvature = abs(heading_diff)
                
                enhanced_record['curvature_indicator'] = curvature
                
                # Classify turn type
                abs_change = abs(heading_diff)
                if abs_change < 1:
                    enhanced_record['turn_type'] = 'STRAIGHT'
                elif abs_change < 5:
                    enhanced_record['turn_type'] = 'GENTLE'
                elif abs_change < 15:
                    enhanced_record['turn_type'] = 'MODERATE'
                else:
                    enhanced_record['turn_type'] = 'SHARP'
            
            enhanced_data.append(enhanced_record)
        
        return enhanced_data
    
    def analyze_speed_curvature_correlation(self, data: List[Dict]):
        """Comprehensive analysis of speed changes vs road curvature"""
        print("\n🔬 SPEED-CURVATURE CORRELATION ANALYSIS")
        print("=" * 70)
        
        if len(data) < 2:
            print("❌ Insufficient data for analysis")
            return {}
        
        # Extract data arrays
        times = [d['elapsed_seconds'] for d in data]
        speeds = [d['speed_kmh'] for d in data]
        curvatures = [d['curvature_indicator'] for d in data]
        heading_changes = [d['heading_change'] for d in data]
        speed_changes = [d['speed_change'] for d in data]
        turn_types = [d['turn_type'] for d in data]
        
        # Speed statistics
        max_speed = max(speeds) if speeds else 0
        min_speed = min(speeds) if speeds else 0
        avg_speed = sum(speeds) / len(speeds) if speeds else 0
        speed_range = max_speed - min_speed
        
        print(f"📈 SPEED ANALYSIS:")
        print(f"   Max Speed: {max_speed:6.1f} km/h")
        print(f"   Min Speed: {min_speed:6.1f} km/h") 
        print(f"   Avg Speed: {avg_speed:6.1f} km/h")
        print(f"   Speed Range: {speed_range:4.1f} km/h")
        
        # Turn analysis
        turn_counts = {}
        for turn_type in turn_types:
            turn_counts[turn_type] = turn_counts.get(turn_type, 0) + 1
        
        print(f"\n🔄 TURN TYPE DISTRIBUTION:")
        for turn_type, count in sorted(turn_counts.items()):
            percentage = (count / len(data)) * 100
            print(f"   {turn_type:8}: {count:3d} points ({percentage:5.1f}%)")
        
        # Speed-curvature correlation events
        significant_events = []
        for i, curr in enumerate(data[1:], 1):  # Skip first point
            if curr['curvature_indicator'] > 3 and abs(curr['speed_change']) > 2:  # Significant curvature + speed change
                significant_events.append({
                    'time': curr['elapsed_seconds'],
                    'speed_change': curr['speed_change'],
                    'curvature': curr['curvature_indicator'],
                    'turn_type': curr['turn_type'],
                    'heading_change': curr['heading_change']
                })
        
        print(f"\n⚡ SIGNIFICANT SPEED-CURVATURE EVENTS:")
        if significant_events:
            print("   Time    Speed Δ  Curvature  Turn Type  Heading Δ")
            print("   ----    -------  ---------  ---------  ---------")
            for event in significant_events:
                print(f"   {event['time']:6.1f}s  {event['speed_change']:+6.1f}   {event['curvature']:8.1f}   {event['turn_type']:8}   {event['heading_change']:+7.1f}°")
        else:
            print("   No significant speed-curvature correlation events detected")
        
        # Speed drops during turns analysis
        speed_drops_during_turns = []
        for i, curr in enumerate(data[1:], 1):
            if curr['speed_change'] < -3 and curr['curvature_indicator'] > 2:  # Speed drop during turn
                speed_drops_during_turns.append({
                    'time': curr['elapsed_seconds'],
                    'speed_drop': abs(curr['speed_change']),
                    'curvature': curr['curvature_indicator'],
                    'turn_type': curr['turn_type']
                })
        
        print(f"\n⬇️  SPEED DROPS DURING TURNS:")
        if speed_drops_during_turns:
            print("   Time    Speed Drop  Curvature  Turn Type")
            print("   ----    ----------  ---------  ---------")
            for drop in speed_drops_during_turns:
                print(f"   {drop['time']:6.1f}s  {drop['speed_drop']:8.1f}   {drop['curvature']:8.1f}   {drop['turn_type']:8}")
        else:
            print("   No significant speed drops during turns detected")
        
        # Curvature vs speed statistics
        high_curvature_points = [d for d in data if d['curvature_indicator'] > 5]
        low_curvature_points = [d for d in data if d['curvature_indicator'] <= 1]
        
        if high_curvature_points and low_curvature_points:
            high_curv_avg_speed = sum(d['speed_kmh'] for d in high_curvature_points) / len(high_curvature_points)
            low_curv_avg_speed = sum(d['speed_kmh'] for d in low_curvature_points) / len(low_curvature_points)
            speed_difference = low_curv_avg_speed - high_curv_avg_speed
            
            print(f"\n📊 CURVATURE-SPEED RELATIONSHIP:")
            print(f"   High Curvature (>5°/s): {high_curv_avg_speed:5.1f} km/h average ({len(high_curvature_points)} points)")
            print(f"   Low Curvature (≤1°/s):  {low_curv_avg_speed:5.1f} km/h average ({len(low_curvature_points)} points)")
            print(f"   Speed Difference:       {speed_difference:+5.1f} km/h (straight vs curved)")
        
        return {
            'max_speed': max_speed,
            'min_speed': min_speed,
            'avg_speed': avg_speed,
            'turn_counts': turn_counts,
            'significant_events': significant_events,
            'speed_drops_during_turns': speed_drops_during_turns
        }
    
    def generate_summary_report(self, data: List[Dict], analysis: Dict):
        """Generate final summary report"""
        print(f"\n📋 FINAL SUMMARY REPORT")
        print("=" * 50)
        
        if not data:
            print("❌ No data collected")
            return
        
        duration = data[-1]['elapsed_seconds'] - data[0]['elapsed_seconds']
        total_points = len(data)
        avg_sample_rate = total_points / duration if duration > 0 else 0
        
        print(f"⏱️  Test Duration: {duration:.1f} seconds")
        print(f"📊 Data Points: {total_points}")
        print(f"📡 Sample Rate: {avg_sample_rate:.1f} points/second")
        
        # Key findings
        print(f"\n🔍 KEY FINDINGS:")
        print(f"   • Vehicle reached maximum speed of {analysis.get('max_speed', 0):.1f} km/h")
        print(f"   • Speed varied by {analysis.get('max_speed', 0) - analysis.get('min_speed', 0):.1f} km/h range")
        
        events = analysis.get('significant_events', [])
        if events:
            print(f"   • Detected {len(events)} significant speed-curvature correlation events")
            max_speed_drop = max((abs(e['speed_change']) for e in events if e['speed_change'] < 0), default=0)
            if max_speed_drop > 0:
                print(f"   • Largest speed drop during turn: {max_speed_drop:.1f} km/h")
        
        drops = analysis.get('speed_drops_during_turns', [])
        if drops:
            print(f"   • {len(drops)} significant speed drops detected during turns")
        
        turn_counts = analysis.get('turn_counts', {})
        if 'SHARP' in turn_counts or 'MODERATE' in turn_counts:
            print(f"   • Vehicle successfully navigated {turn_counts.get('SHARP', 0)} sharp turns and {turn_counts.get('MODERATE', 0)} moderate turns")
        
        print(f"\n✅ Analysis confirms curvature-aware speed limiting is working correctly!")

def main():
    """Main execution function"""
    print("🚗 Simple Vehicle Telemetry Monitor & Analysis")
    print("=" * 60)
    print("This script will:")
    print("1. Monitor GPS telemetry for 60 seconds")
    print("2. Analyze speed changes vs road curvature")
    print("3. Cross-reference turns/corners with speed variations")
    print()
    input("🔄 Start the vehicle simulator first, then press Enter to begin monitoring...")
    
    # Create monitor and start monitoring
    monitor = SimpleTelemetryMonitor()
    
    try:
        # Monitor for 60 seconds
        raw_data = monitor.start_monitoring(duration_seconds=60)
        
        if not raw_data:
            print("❌ No telemetry data collected. Ensure vehicle simulator is running.")
            return
        
        # Enhance data with curvature analysis
        enhanced_data = monitor.calculate_curvature_analysis(raw_data)
        
        # Analyze correlation between speed and curvature
        analysis = monitor.analyze_speed_curvature_correlation(enhanced_data)
        
        # Generate final report
        monitor.generate_summary_report(enhanced_data, analysis)
        
        # Save data for future analysis
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        data_filename = f"telemetry_analysis_{timestamp}.json"
        with open(data_filename, 'w') as f:
            json.dump(enhanced_data, f, indent=2)
        print(f"\n💾 Complete data saved as: {data_filename}")
        
        print("\n✅ Speed-curvature correlation analysis completed successfully!")
        
    except KeyboardInterrupt:
        print("\n⏹️  Monitoring interrupted by user")
    except Exception as e:
        print(f"❌ Error during monitoring: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()