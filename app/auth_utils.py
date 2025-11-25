import jwt
from jwt import PyJWKClient
from fastapi import HTTPException
from typing import Any, Dict

JWKS_URL = "https://pinket.com/auth-server/.well-known/jwks.json"
ALLOWED_ALGS = ["RS256", "RS512", "HS256"]


def extract_uid_from_jwt(token: str) -> Dict[str, Any]:
    try:
        unverified = jwt.get_unverified_header(token)
        alg = unverified.get("alg")
        if alg not in ALLOWED_ALGS:
            raise HTTPException(status_code=401, detail=f"Unsupported alg: {alg}")

        jwk_client = PyJWKClient(JWKS_URL)
        signing_key = jwk_client.get_signing_key_from_jwt(token)
        decoded = jwt.decode(token, signing_key.key, algorithms=[alg], options={"verify_exp": True})

        uid = decoded.get("sub") or decoded.get("uid") or decoded.get("user_id")
        if not uid:
            raise HTTPException(status_code=400, detail="UID not found in token claims")

        return {"uid": uid, "claims": decoded}

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
