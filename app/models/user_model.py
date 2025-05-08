from builtins import bool, int, str
from typing import Optional
from datetime import datetime
import uuid
from sqlalchemy import (
    Column, String, Integer, DateTime, Boolean, func
)
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.orm import Mapped, mapped_column, validates
from app.database import Base
from enum import Enum
from urllib.parse import urlparse




class UserRole(Enum):
    """Enumeration of user roles within the application, stored as ENUM in the database."""
    ANONYMOUS = "ANONYMOUS"
    AUTHENTICATED = "AUTHENTICATED"
    MANAGER = "MANAGER"
    ADMIN = "ADMIN"




class User(Base):
    """
    Represents a user within the application, corresponding to the 'users' table in the database.
    This class uses SQLAlchemy ORM for mapping attributes to database columns efficiently.
    """
    __tablename__ = "users"
    __mapper_args__ = {"eager_defaults": True}


    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nickname: Mapped[str] = Column(String(50), unique=True, nullable=False, index=True)
    email: Mapped[str] = Column(String(255), unique=True, nullable=False, index=True)
    first_name: Mapped[str] = Column(String(100), nullable=True)
    last_name: Mapped[str] = Column(String(100), nullable=True)
    bio: Mapped[str] = Column(String(500), nullable=True)
    profile_picture_url: Mapped[str] = Column(String(255), nullable=True)
    linkedin_profile_url: Mapped[str] = Column(String(255), nullable=True)
    github_profile_url: Mapped[str] = Column(String(255), nullable=True)
    location: Mapped[Optional[str]] = Column(String(255), nullable=True)
    role: Mapped[UserRole] = Column(ENUM(UserRole, name='UserRole', create_constraint=True), nullable=False)
    is_professional: Mapped[bool] = Column(Boolean, default=False)
    professional_status_updated_at: Mapped[datetime] = Column(DateTime(timezone=True), nullable=True)
    last_login_at: Mapped[datetime] = Column(DateTime(timezone=True), nullable=True)
    failed_login_attempts: Mapped[int] = Column(Integer, default=0)
    is_locked: Mapped[bool] = Column(Boolean, default=False)
    created_at: Mapped[datetime] = Column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    verification_token = Column(String, nullable=True)
    email_verified: Mapped[bool] = Column(Boolean, default=False, nullable=False)
    hashed_password: Mapped[str] = Column(String(255), nullable=False)




    @validates('email')
    def validate_email(self, key, email):
        """Ensures that the email follows proper format."""
        if '@' not in email:
            raise ValueError("Invalid email format")
        return email


    @validates('github_profile_url', 'linkedin_profile_url')
    def validate_url(self, key, url):
        """Validates that profile URLs are valid if provided."""
        if url and not (url.startswith('http://') or url.startswith('https://')):
            raise ValueError(f"Invalid URL format for {key}")
        return str(url) if url else url  # Convert URL to string


    def __repr__(self) -> str:
        """Provides a readable representation of a user object."""
        return f"<User {self.nickname}, Role: {self.role.name}>"


    # Method for updating profile information
    def update_profile(self, first_name: str, last_name: str, bio: str, profile_picture_url: str, location: Optional[str] = None, linkedin_profile_url: Optional[str] = None, github_profile_url: Optional[str] = None):
        """Updates user profile fields."""
        # Update basic profile fields
        self.first_name = first_name
        self.last_name = last_name
        self.bio = bio
        self.profile_picture_url = profile_picture_url


        # Convert profile URLs to strings (if provided)
        if linkedin_profile_url:
            self.linkedin_profile_url = str(linkedin_profile_url)
        if github_profile_url:
            self.github_profile_url = str(github_profile_url)


        # Update location if provided
        if location:
            self.location = location


        # Ensure the updated_at timestamp is refreshed
        self.updated_at = func.now()


    def lock_account(self):
        """Locks the user account."""
        self.is_locked = True


    def unlock_account(self):
        """Unlocks the user account."""
        self.is_locked = False


    def verify_email(self):
        """Marks the user's email as verified."""
        self.email_verified = True


    def has_role(self, role_name: UserRole) -> bool:
        """Checks if the user has a specified role."""
        return self.role == role_name


    def update_professional_status(self, status: bool):
        """Updates the professional status and logs the update time."""
        self.is_professional = status
        self.professional_status_updated_at = func.now()
