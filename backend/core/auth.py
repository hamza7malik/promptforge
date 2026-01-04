from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
from functools import lru_cache
from config.settings import settings
from core.logging import logger

security = HTTPBearer()


class Auth0Verifier:
    """Auth0 JWT token verification"""
    
    def __init__(self):
        self.domain = settings.AUTH0_DOMAIN
        self.audience = settings.AUTH0_AUDIENCE
        self.issuer = settings.AUTH0_ISSUER
        self.algorithms = settings.AUTH0_ALGORITHMS
        self._jwks: Optional[dict] = None
        self._jwks_expiry: Optional[datetime] = None
        
    async def get_jwks(self) -> dict:
        """Fetch JWKS from Auth0 with caching"""
        if self._jwks and self._jwks_expiry and datetime.utcnow() < self._jwks_expiry:
            return self._jwks
            
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"https://{self.domain}/.well-known/jwks.json")
                response.raise_for_status()
                self._jwks = response.json()
                self._jwks_expiry = datetime.utcnow() + timedelta(hours=24)
                return self._jwks
            except Exception as e:
                logger.error("Failed to fetch JWKS", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Authentication service unavailable"
                )
    
    def get_signing_key(self, token: str, jwks: dict):
        """Extract signing key from JWKS"""
        try:
            unverified_header = jwt.get_unverified_header(token)
            rsa_key = {}
            
            for key in jwks["keys"]:
                if key["kid"] == unverified_header["kid"]:
                    rsa_key = {
                        "kty": key["kty"],
                        "kid": key["kid"],
                        "use": key["use"],
                        "n": key["n"],
                        "e": key["e"]
                    }
                    break
                    
            if not rsa_key:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Unable to find appropriate signing key"
                )
                
            return rsa_key
        except Exception as e:
            logger.error("Error getting signing key", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token header"
            )
    
    async def verify_token(self, token: str) -> dict:
        """Verify and decode JWT token"""
        try:
            jwks = await self.get_jwks()
            signing_key = self.get_signing_key(token, jwks)
            
            payload = jwt.decode(
                token,
                signing_key,
                algorithms=self.algorithms,
                audience=self.audience,
                issuer=self.issuer
            )
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.JWTClaimsError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token claims"
            )
        except JWTError as e:
            logger.error("JWT verification failed", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )


@lru_cache()
def get_auth0_verifier() -> Auth0Verifier:
    return Auth0Verifier()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    verifier: Auth0Verifier = Depends(get_auth0_verifier)
) -> dict:
    """Dependency to get current authenticated user"""
    token = credentials.credentials
    payload = await verifier.verify_token(token)
    return payload


async def get_current_user_id(
    current_user: dict = Depends(get_current_user)
) -> str:
    """Extract user ID from token payload"""
    user_id = current_user.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID not found in token"
        )
    return user_id
