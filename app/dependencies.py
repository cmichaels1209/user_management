from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import Database
from app.utils.template_manager import TemplateManager
from app.services.email_service import EmailService
from settings.config import Settings
from app.services.jwt_service import decode_token
from app.models.user_model import UserRole

# Import the User class here to fix the NameError
from app.models.user_model import User  # <-- Add this import to resolve the NameError

def get_settings() -> Settings:
    """Return application settings."""
    return Settings()

def get_email_service() -> EmailService:
    """Get the email service dependency."""
    template_manager = TemplateManager()
    return EmailService(template_manager=template_manager)

async def get_db() -> AsyncSession:
    """Dependency that provides a database session for each request."""
    async_session_factory = Database.get_session_factory()
    async with async_session_factory() as session:
        try:
            yield session
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

# OAuth2PasswordBearer is used to handle the OAuth2 password flow
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    """
    Get the current user based on the provided OAuth2 token.
    This will verify the token and fetch the user's information from the database.
    """
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Decode the token to get user information
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception

    user_id: str = payload.get("sub")
    user_role: str = payload.get("role")

    print(f"Decoded token: {payload}")  # Debugging: Add this for debugging

    if user_id is None or user_role is None:
        raise credentials_exception

    # Lazy import UserService here to avoid circular import issues
    from app.services.user_service import UserService  # Move import here to avoid circular import

    # Fetch the user from the database using UserService
    user = await UserService.get_by_id(db, user_id)
    if not user:
        raise credentials_exception

    return user


def require_role(roles: list):
    """
    Dependency that checks if the current user has one of the required roles.
    If the user does not have the required role, a 403 error is raised.
    """
    def role_checker(current_user: User = Depends(get_current_user)):  # Ensure current_user is typed as User
        print(f"User Role: {current_user.role}")  # Debugging line
        allowed_roles = [UserRole[role] for role in roles]  # Convert strings to UserRole enum values
        if current_user.role not in allowed_roles:  # Compare Enum values
            raise HTTPException(status_code=403, detail="Operation not permitted")
        return current_user
    return role_checker