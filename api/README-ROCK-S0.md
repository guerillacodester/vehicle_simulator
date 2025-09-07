# Fleet Management API - Rock S0 Deployment

🚀 **Professional fleet management system for Rock S0 single-board computer**

## 🎯 Quick Start

### 1. Setup (One-time)
```bash
# Make setup script executable
chmod +x setup

# Run setup (installs all dependencies)
./setup
```

### 2. Run the API
```bash
# Option 1: Using the start script
./start

# Option 2: Direct execution
./main.py

# Option 3: With virtual environment
source venv/bin/activate
python3 main.py
```

### 3. Access the Interface
```
Web Interface: http://your-rock-s0-ip:8000/fleet-management
API Docs:      http://your-rock-s0-ip:8000/docs
Health Check:  http://your-rock-s0-ip:8000/
```

## 🔧 System Requirements

### Hardware
- **Rock S0** (or compatible ARM64 SBC)
- **RAM:** 1GB minimum, 2GB+ recommended
- **Storage:** 8GB minimum, 16GB+ recommended
- **Network:** Ethernet or WiFi connection

### Software
- **OS:** Ubuntu/Debian-based Linux
- **Python:** 3.8+ (automatically installed by setup)
- **Dependencies:** Installed by setup script

## 📦 What Gets Installed

### System Packages
- `python3` - Python runtime
- `python3-pip` - Package manager
- `python3-venv` - Virtual environments
- `libpq-dev` - PostgreSQL development headers
- `build-essential` - Compilation tools

### Python Packages
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `python-multipart` - File upload support
- `sqlalchemy` - Database ORM
- `sshtunnel` - Secure database connections
- And more (see requirements.txt)

## 🎛️ Configuration

### Database Connection
The API connects to PostgreSQL via SSH tunnel. Configuration is in:
```
config/database.py
```

### Port Configuration
Default port: 8000
To change: Edit `main.py` line with `uvicorn.run(..., port=8000)`

## 📁 File Structure
```
api/
├── main.py              # Main application (executable)
├── start                # Start script (executable)
├── setup                # Setup script (executable)
├── requirements.txt     # Python dependencies
├── templates/           # HTML templates
├── static/             # CSS, JS, assets
├── fleet_management/   # Core business logic
└── sample_data/        # Sample files for testing
```

## 🔄 Service Management

### Systemd Service (Optional)
If you chose to install the systemd service during setup:

```bash
# Start the service
sudo systemctl start fleet-api

# Stop the service
sudo systemctl stop fleet-api

# Check status
sudo systemctl status fleet-api

# View logs
sudo journalctl -u fleet-api -f

# Auto-start on boot
sudo systemctl enable fleet-api
```

### Manual Management
```bash
# Start manually
./start

# Stop with Ctrl+C
# Or kill process:
pkill -f "python.*main.py"
```

## 📊 Monitoring

### Health Check
```bash
curl http://localhost:8000/
```

### API Status
```bash
curl http://localhost:8000/fleet/countries
```

### System Resources
```bash
# CPU and memory usage
top

# Disk usage
df -h

# Network connections
netstat -tulpn | grep :8000
```

## 🚨 Troubleshooting

### Port Already in Use
```bash
# Find what's using port 8000
sudo lsof -i :8000

# Kill the process
sudo kill $(sudo lsof -t -i:8000)
```

### Permission Issues
```bash
# Make scripts executable
chmod +x start main.py setup

# Fix ownership
sudo chown -R $USER:$USER .
```

### Python Dependencies
```bash
# Reinstall dependencies
source venv/bin/activate
pip install -r requirements.txt --force-reinstall
```

### Database Connection Issues
- Check network connectivity to database server
- Verify SSH credentials in `config/database.py`
- Ensure PostgreSQL server is running

## 🔐 Security

### Firewall
```bash
# Allow port 8000
sudo ufw allow 8000

# Check firewall status
sudo ufw status
```

### Access Control
- The API runs on all interfaces (0.0.0.0)
- Consider using a reverse proxy (nginx) for production
- Implement authentication if needed

## 📈 Performance

### Rock S0 Optimization
- Uses async/await for better performance
- Database connection pooling
- Efficient file processing
- Minimal memory footprint

### Scaling
- Increase worker processes in production
- Use nginx for load balancing
- Consider Redis for caching

## 🆘 Support

### Logs Location
```bash
# Application logs
journalctl -u fleet-api

# System logs
tail -f /var/log/syslog
```

### Debug Mode
Edit `main.py` and set:
```python
uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="debug")
```

---

**🎉 Your Fleet Management API is now ready for production on Rock S0!**
