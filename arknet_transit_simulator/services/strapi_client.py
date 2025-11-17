import aiohttp
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class AuthenticationError(Exception):
    pass

class StrapiClient:
    """
    Centralized authenticated HTTP client for Strapi API access.
    Features:
    - Single authentication point (JWT)
    - Shared aiohttp session and connection pool
    - Automatic token refresh
    - Consistent error handling
    """
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self._session: Optional[aiohttp.ClientSession] = None
        self._token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None

    async def initialize(self):
        """Initialize session and authenticate"""
        self._session = aiohttp.ClientSession()
        await self._authenticate()

    async def _authenticate(self):
        """Authenticate and obtain JWT token"""
        async with self._session.post(
            f"{self.base_url}/api/auth/local",
            json={"identifier": self.username, "password": self.password}
        ) as response:
            if response.status == 200:
                data = await response.json()
                self._token = data.get("jwt")
                self._token_expiry = datetime.now() + timedelta(hours=24)
                logger.info("[StrapiClient] Authenticated successfully")
            else:
                logger.error(f"[StrapiClient] Auth failed: HTTP {response.status}")
                raise AuthenticationError(f"Auth failed: HTTP {response.status}")

    def _get_headers(self) -> Dict[str, str]:
        """Get authenticated headers"""
        if not self._token:
            raise AuthenticationError("No JWT token available")
        return {"Authorization": f"Bearer {self._token}"}

    async def get(self, endpoint: str, **kwargs) -> Any:
        """Make authenticated GET request"""
        if not self._session:
            raise RuntimeError("Session not initialized")
        if not self._token or datetime.now() >= self._token_expiry:
            await self._authenticate()
        async with self._session.get(
            f"{self.base_url}{endpoint}",
            headers=self._get_headers(),
            **kwargs
        ) as response:
            if response.status == 403:
                logger.error(f"[StrapiClient] 403 Forbidden: {endpoint}")
                raise PermissionError(f"Access denied to {endpoint}")
            response.raise_for_status()
            return await response.json()

    async def close(self):
        """Close session"""
        if self._session:
            await self._session.close()
            self._session = None
