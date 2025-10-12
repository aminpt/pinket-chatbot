import httpx
from typing import Any, Dict, Optional


class APIClient:
    """
    Low‑level wrapper around httpx.

    It is deliberately *stateless*: headers are assembled fresh on every call,
    so wider applications can share a single instance safely.
    """

    def __init__(self, base_url: str = "https://pinket.com/api") -> None:
        self.base_url = base_url.rstrip("/")

        # These never change between requests
        self._static_headers: Dict[str, str] = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N)",
        }

    def make_request(
        self,
        endpoint: str,
        *,
        method: str = "GET",
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        token: str,
        timeout: float = 10.0,
    ):
        """Send an HTTP request and return the decoded JSON payload."""
        headers = {**self._static_headers, "Authorization": f"Bearer {token}"}
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        with httpx.Client(timeout=timeout) as client:
            if method == "GET":
                resp = client.get(url, params=params, headers=headers)
            elif method == "POST":
                resp = client.post(url, json=data, headers=headers)
            elif method == "PUT":
                resp = client.put(url, json=data, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

        resp.raise_for_status()
        return resp.json()
