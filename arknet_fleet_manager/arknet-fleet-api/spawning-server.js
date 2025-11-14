const express = require('express');
const { spawn } = require('child_process');
const path = require('path');
const cors = require('cors');

const app = express();
const PORT = 3001; // Different port from Strapi

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static('public'));

// API endpoint to call the Python spawning script
app.post('/api/passenger-spawning/generate', async (req, res) => {
    try {
        const { hour, time_window_minutes } = req.body;
        
        console.log(`🚀 Spawning request: hour ${hour}, window ${time_window_minutes} minutes`);
        
        // Call the Python script
        const python = spawn('python', ['database_spawning_api.py', hour || 8, time_window_minutes || 5]);
        
        let data = '';
        let errorData = '';
        
        python.stdout.on('data', (chunk) => {
            data += chunk.toString();
        });
        
        python.stderr.on('data', (chunk) => {
            errorData += chunk.toString();
        });
        
        python.on('close', (code) => {
            if (code !== 0) {
                console.error(`Python script failed with code ${code}`);
                console.error('Error:', errorData);
                return res.status(500).json({ 
                    error: 'Python script failed', 
                    details: errorData,
                    code: code 
                });
            }
            
            try {
                console.log('Raw Python output length:', data.length);
                console.log('Last 200 chars:', data.substring(data.length - 200));
                
                let result = null;
                
                // Find the JSON object - it's between the last occurrence of {"passengers" and the closing }
                const startPattern = '{"passengers":';
                const lastJsonStart = data.lastIndexOf(startPattern);
                
                if (lastJsonStart !== -1) {
                    // Find the matching closing brace
                    let jsonStr = '';
                    let braceCount = 0;
                    let foundStart = false;
                    
                    for (let i = lastJsonStart; i < data.length; i++) {
                        const char = data[i];
                        jsonStr += char;
                        
                        if (char === '{') {
                            braceCount++;
                            foundStart = true;
                        } else if (char === '}') {
                            braceCount--;
                            if (foundStart && braceCount === 0) {
                                break;
                            }
                        }
                    }
                    
                    console.log('Extracted JSON length:', jsonStr.length);
                    console.log('JSON preview:', jsonStr.substring(0, 100) + '...');
                    
                    result = JSON.parse(jsonStr.trim());
                    console.log('Successfully parsed JSON with', result.passengers?.length, 'passengers');
                }
                
                if (result && result.passengers) {
                    // Convert the format to match what the visualizer expects
                    const passengers = result.passengers || [];
                    const spawnRequests = passengers.map(passenger => ({
                        latitude: passenger.latitude,
                        longitude: passenger.longitude,
                        spawn_type: passenger.spawn_type,
                        location_name: passenger.location_name || `${passenger.spawn_type} spawn`,
                        zone_type: passenger.zone_type || passenger.spawn_type,
                        spawn_rate: passenger.spawn_rate || 1.0,
                        minute: passenger.minute || 0,
                        poi_id: passenger.poi_id || null,
                        depot_id: passenger.depot_id || null,
                        route_id: passenger.route_id || null
                    }));
                    
                    console.log(`✅ Generated ${spawnRequests.length} spawn requests`);
                    console.log(`📊 Hour ${result.hour}, Total: ${result.total_passengers}`);
                    
                    res.json({
                        success: true,
                        spawn_requests: spawnRequests,
                        total_passengers: result.total_passengers,
                        hour: result.hour,
                        time_window_minutes: result.time_window_minutes
                    });
                } else {
                    console.error('Could not find JSON result in Python output');
                    res.status(500).json({ 
                        error: 'Could not parse Python script output',
                        output: data
                    });
                }
            } catch (parseError) {
                console.error('JSON parse error:', parseError);
                res.status(500).json({ 
                    error: 'Failed to parse Python script result', 
                    details: parseError.message,
                    output: data
                });
            }
        });
        
    } catch (error) {
        console.error('Server error:', error);
        res.status(500).json({ 
            error: 'Internal server error', 
            details: error.message 
        });
    }
});

// Health check endpoint
app.get('/api/health', (req, res) => {
    res.json({ 
        status: 'ok', 
        service: 'Passenger Spawning API Server',
        timestamp: new Date().toISOString()
    });
});

// Start server
app.listen(PORT, () => {
    console.log(`🚀 Passenger Spawning API Server running on http://localhost:${PORT}`);
    console.log(`📊 Visit http://localhost:${PORT}/passenger-spawning-visualization.html to view the visualizer`);
    console.log(`🔗 API endpoint: POST http://localhost:${PORT}/api/passenger-spawning/generate`);
});