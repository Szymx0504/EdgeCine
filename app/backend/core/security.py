import os
from fastapi import Security, HTTPException, Depends
from fastapi.security.api_key import APIKeyHeader
from starlette.status import HTTP_403_FORBIDDEN

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# Get key from environment
API_KEY = os.getenv("API_KEY", "super-secret-admin-key")

async def get_api_key(api_key: str = Security(api_key_header)):
    """
    Dependency to validate the API Key.
    Compares the header X-API-Key with the environment variable.
    """
    if api_key == API_KEY:
        return api_key
    
    raise HTTPException(
        status_code=HTTP_403_FORBIDDEN, 
        detail="Could not validate API Key"
    )
