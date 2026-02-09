from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from corex.config import settings

auth_scheme = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(auth_scheme)):
    if credentials.credentials != settings.SECRET_KEY:
        raise HTTPException(status_code=403, detail="Invalid Resonance Token")
    return credentials.credentials
