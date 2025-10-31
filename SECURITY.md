# Security & Configuration Guide

## Overview

This project separates **sensitive credentials** from **operational configuration** to improve security and maintainability.

## Configuration Architecture

### 📄 `config.ini` - Operational Configuration (Safe to commit)
**Location**: `config.ini` (root directory)

**Contains**:
- Service ports (Strapi, GPS, Geospatial, Manifest)
- Service URLs (localhost endpoints)
- Enable/disable flags for subsystems
- Timing parameters (startup waits, intervals)
- Console spawning preferences

**Purpose**: Operational settings that control how the system runs. Safe to commit to version control and share with team.

**Example**:
```ini
[infrastructure]
strapi_url = http://localhost:1337
strapi_port = 1337
gpscentcom_port = 5000
geospatial_port = 6000

[launcher]
enable_gpscentcom = true
enable_geospatial = true
```

### 🔐 `.env` - Secrets & Credentials (NEVER commit)
**Location**: `.env` (root directory) and `arknet_fleet_manager/arknet-fleet-api/.env`

**Contains**:
- API tokens and authentication keys
- Database passwords
- Cloud service credentials (Cloudinary, AWS, etc.)
- JWT secrets and encryption keys

**Purpose**: Sensitive credentials that must be kept secret. **NEVER** commit to version control.

**Security Status**:
- ✅ Both `.env` files are in `.gitignore`
- ✅ `.env.example` templates provided with placeholder values
- ⚠️ **ACTION REQUIRED**: Change default secrets before production deployment!

### 🗄️ Database (`operational-configurations`) - Runtime Settings
**Location**: Strapi database table `operational-configurations`

**Contains**:
- Spawn rates and intervals
- Continuous mode toggles
- Feature flags (enable route/depot spawners)
- Performance thresholds

**Purpose**: Settings that can be changed at runtime without code deployment. Managed via Strapi admin panel or API.

## File Structure

```
vehicle_simulator/
├── .env                           # Root secrets (API tokens) - NEVER COMMIT
├── .env.example                   # Template for root .env
├── config.ini                     # Operational configuration - SAFE TO COMMIT
├── arknet_fleet_manager/
│   └── arknet-fleet-api/
│       ├── .env                   # Strapi secrets (DB password, JWT) - NEVER COMMIT
│       ├── .env.example           # Template for Strapi .env
│       └── config/
│           ├── server.ts          # Server config (HOST, PORT defaults)
│           ├── database.ts        # Database config (uses .env credentials)
│           └── plugins.ts         # Plugin config (upload provider, etc.)
```

## What Goes Where?

| Type | Location | Example | Commit? |
|------|----------|---------|---------|
| API Tokens | `.env` | `STRAPI_API_TOKEN=abc123` | ❌ NO |
| Database Passwords | `arknet-fleet-api/.env` | `DATABASE_PASSWORD=secret` | ❌ NO |
| Service Ports | `config.ini` | `gpscentcom_port = 5000` | ✅ YES |
| Enable Flags | `config.ini` | `enable_gpscentcom = true` | ✅ YES |
| Spawn Settings | Database | `continuous_mode = true` | ✅ YES (via Strapi) |
| Cloud Credentials | `.env` | `CLOUDINARY_SECRET=xyz` | ❌ NO |

## Security Checklist

### ⚠️ Before Production Deployment:

- [ ] **Change all default secrets** in `arknet-fleet-api/.env`:
  - [ ] `APP_KEYS` (generate unique keys)
  - [ ] `API_TOKEN_SALT`
  - [ ] `ADMIN_JWT_SECRET`
  - [ ] `JWT_SECRET`
  - [ ] `ENCRYPTION_KEY`
  - [ ] `DATABASE_PASSWORD`

- [ ] **Verify `.gitignore`**:
  - [ ] `.env` is excluded (root)
  - [ ] `arknet-fleet-api/.env` is excluded

- [ ] **Review exposed credentials**:
  - [ ] No secrets in `config.ini`
  - [ ] No secrets in committed code
  - [ ] No secrets in documentation

- [ ] **Set proper file permissions** (Linux/Mac):
  ```bash
  chmod 600 .env
  chmod 600 arknet_fleet_manager/arknet-fleet-api/.env
  ```

## Environment Setup

### First Time Setup:

1. **Copy environment templates**:
   ```bash
   cp .env.example .env
   cp arknet_fleet_manager/arknet-fleet-api/.env.example arknet_fleet_manager/arknet-fleet-api/.env
   ```

2. **Edit `.env` files** with real credentials:
   - Database passwords
   - API tokens
   - Cloud service keys

3. **Configure operational settings** in `config.ini`:
   - Service ports
   - Enable/disable subsystems
   - Development vs production modes

4. **Seed operational configuration** database:
   ```bash
   cd arknet_fleet_manager
   python seed_operational_config.py
   ```

## Common Issues

### ❌ "Configuration file not found: config.ini"
**Solution**: Ensure `config.ini` exists in the project root. Copy from `config.ini.example` if needed.

### ❌ "Database authentication failed"
**Solution**: Check `DATABASE_USERNAME` and `DATABASE_PASSWORD` in `arknet-fleet-api/.env`.

### ❌ "STRAPI_API_TOKEN not found"
**Solution**: If using Strapi authentication, generate a token in Strapi admin panel and add to root `.env`.

## Best Practices

1. **Never hardcode secrets** in source code
2. **Use `.env` files only for secrets**, not operational config
3. **Document all configuration** in this file when adding new settings
4. **Rotate secrets regularly** in production
5. **Use different credentials** for development vs production
6. **Keep `.env.example` updated** when adding new environment variables

## Generating Secure Secrets

### For Strapi secrets (APP_KEYS, JWT_SECRET, etc.):
```bash
# Generate random base64 string (Linux/Mac)
openssl rand -base64 32

# Generate random hex string
openssl rand -hex 32
```

### For API tokens:
```bash
# Generate UUID
python -c "import uuid; print(uuid.uuid4())"
```

## Support

If you discover a security vulnerability, please email: security@example.com

For configuration questions, see: `CONTEXT.md` and `TODO.md`
