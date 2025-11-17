import aiohttp
import logging

class StrapiAuthClient:
    def __init__(self, api_base_url: str, username: str, password: str):
        self.api_base_url = api_base_url.rstrip('/')
        self.username = username
        self.password = password
        self.jwt_token = None
        self.session = aiohttp.ClientSession()

    async def login(self):
        url = f"{self.api_base_url}/api/auth/local"
        payload = {
            "identifier": self.username,
            "password": self.password
        }
        async with self.session.post(url, json=payload) as response:
            if response.status == 200:
                data = await response.json()
                self.jwt_token = data.get("jwt")
                logging.info(f"Strapi login successful for {self.username}")
                logging.info(f"JWT token stored: {self.jwt_token[:20]}..." if self.jwt_token else "JWT token is None")
                return self.jwt_token
            else:
                logging.error(f"Strapi login failed: {response.status}")
                return None

    async def logout(self):
        self.jwt_token = None
        await self.session.close()
        logging.info("Strapi session closed and token cleared.")

    def get_auth_header(self):
        if self.jwt_token:
            header = {"Authorization": f"Bearer {self.jwt_token}"}
            logging.debug(f"Returning auth header with token: {self.jwt_token[:30]}...")
            return header
        logging.warning("get_auth_header called but no JWT token available")
        return {}
