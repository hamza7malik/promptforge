from fastapi import APIRouter

router = APIRouter()


@router.get("/me")
async def get_current_user():
    """Get current authenticated user"""
    # This is a placeholder - auth is handled by Auth0 JWT verification
    return {"message": "User authenticated via Auth0"}


@router.post("/callback")
async def auth_callback():
    """Handle Auth0 callback"""
    return {"message": "Auth callback handled by frontend"}
