"""
Auth0 OAuth2 JWT authentication for Extraction Job API.
"""

import os
from typing import Callable

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient

# HTTPBearer for Swagger UI Authorize button
http_bearer = HTTPBearer(description="Auth0 JWT token")

# Configuration with env fallbacks
AUTH0_DOMAIN = os.environ.get(
    "AUTH0_DOMAIN", "dev-wkl17exhgoi6mj0m.us.auth0.com"
)
AUTH0_AUDIENCE = os.environ.get(
    "AUTH0_AUDIENCE", "https://dev-wkl17exhgoi6mj0m.us.auth0.com/api/v2/"
)
JWKS_URL = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"
ISSUER = f"https://{AUTH0_DOMAIN}/"

# Cached JWKS client (reused across requests)
_jwks_client: PyJWKClient | None = None


def _get_jwks_client() -> PyJWKClient:
    global _jwks_client
    if _jwks_client is None:
        _jwks_client = PyJWKClient(JWKS_URL, cache_jwk_set=True)
    return _jwks_client


def _validate_token(token: str) -> dict:
    """Validate JWT token. Raises HTTPException if invalid."""
    try:
        jwks_client = _get_jwks_client()
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=AUTH0_AUDIENCE,
            issuer=ISSUER,
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def verify_token(request: Request) -> dict:
    """Validate Bearer token from Authorization header. Raises 401 if invalid."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = auth_header[7:].strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return _validate_token(token)


def verify_token_with_bearer(
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
) -> dict:
    """Validate Bearer token via HTTPBearer (enables Swagger Authorize button)."""
    return _validate_token(credentials.credentials)


def no_auth(request: Request) -> None:
    """No-op dependency when AUTH_DISABLED is set."""
    return None


def get_auth_dependency() -> Callable:
    """Return verify_token_with_bearer or no_auth based on AUTH_DISABLED env var."""
    if os.environ.get("AUTH_DISABLED", "").lower() in ("1", "true", "yes"):
        return no_auth
    return verify_token_with_bearer
