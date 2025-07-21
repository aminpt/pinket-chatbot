# app/services/api_client.py

import httpx

class APIClient:
    def __init__(self):
        self.base_url = "https://pinket.com/api/cu"
        self.headers = {
            "Authorization": "Bearer <YOUR_BEARER_TOKEN>",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N)",
        }

    async def make_request(self, endpoint, method="GET", params=None, data=None):
        async with httpx.AsyncClient() as client:
            url = f"{self.base_url}/{endpoint}"
            if method == "GET":
                response = await client.get(url, params=params, headers=self.headers)
            elif method == "POST":
                response = await client.post(url, json=data, headers=self.headers)
            elif method == "PUT":
                response = await client.put(url, json=data, headers=self.headers)
            return response.json()
