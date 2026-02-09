# corex.auth package
from fastapi import HTTPException, Header
from typing import Optional
import os

# Simple token verification for MVP
API_TOKEN = os.getenv("LUMEN_API_TOKEN", "")
if not API_TOKEN and os.getenv("LUMEN_DEV_MODE", "true").lower() != "true":
    raise ValueError("LUMEN_API_TOKEN must be set in production mode")


async def verify_token(authorization: Optional[str] = Header(None)) -> str:
    """Verify API token from Authorization header."""
    if not authorization:
        # Allow unauthenticated access in dev mode
        if os.getenv("LUMEN_DEV_MODE", "true").lower() == "true":
            return "dev_user"
        raise HTTPException(status_code=401, detail="Authorization header required")

    # Extract token from "Bearer <token>" format
    parts = authorization.split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        token = parts[1]
    else:
        token = authorization

    if token != API_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid token")

    return token


def create_token(user_id: str) -> str:
    """Create a simple token (for MVP - use JWT in production)."""
    return f"{API_TOKEN}_{user_id}"
