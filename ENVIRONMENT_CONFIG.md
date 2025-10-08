# Environment Configuration Guide

## Quick Setup

1. **Copy the example file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` for your setup:**

### Development (Local Strapi)
```bash
ARKNET_API_URL=http://localhost:1337
STRAPI_API_TOKEN=your_local_dev_token
```

### Your OVH Server
```bash
ARKNET_API_URL=http://your-ovh-server-ip:1337
STRAPI_API_TOKEN=your_production_token
```

### Custom Domain
```bash
ARKNET_API_URL=https://transit.yourdomain.com
STRAPI_API_TOKEN=your_production_token
```

## Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `ARKNET_API_URL` | Strapi API base URL | `http://localhost:1337` | No |
| `STRAPI_API_TOKEN` | API authentication token | None | Recommended |

## Usage

The `ProductionApiDataSource` will automatically use these environment variables:

```python
# Uses ARKNET_API_URL from .env or defaults to localhost:1337
data_source = ProductionApiDataSource()

# Or override for specific cases
data_source = ProductionApiDataSource(base_url="http://custom-server:1337")
```

## Security

- **Never commit `.env` files** - they're in `.gitignore`
- **Use strong API tokens** for production
- **Use HTTPS** for production deployments