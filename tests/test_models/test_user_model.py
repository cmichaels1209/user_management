from builtins import repr
from datetime import datetime, timezone
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user_model import User, UserRole
from app.services.user_service import UserService
from app.utils.security import hash_password


@pytest.mark.asyncio
async def test_user_role(db_session: AsyncSession, user: User, admin_user: User, manager_user: User):
    """
    Tests that the default role is assigned correctly and can be updated.
    """
    assert user.role == UserRole.AUTHENTICATED, "Default role should be USER"
    assert admin_user.role == UserRole.ADMIN, "Admin role should be correctly assigned"
    assert manager_user.role == UserRole.MANAGER, "Pro role should be correctly assigned"

@pytest.mark.asyncio
async def test_has_role(user: User, admin_user: User, manager_user: User):
    """
    Tests the has_role method to ensure it accurately checks the user's role.
    """
    assert user.has_role(UserRole.AUTHENTICATED), "User should have USER role"
    assert not user.has_role(UserRole.ADMIN), "User should not have ADMIN role"
    assert admin_user.has_role(UserRole.ADMIN), "Admin user should have ADMIN role"
    assert manager_user.has_role(UserRole.MANAGER), "Pro user should have PRO role"

@pytest.mark.asyncio
async def test_user_repr(user: User):
    """
    Tests the __repr__ method for accurate representation of the User object.
    """
    assert repr(user) == f"<User {user.nickname}, Role: {user.role.name}>", "__repr__ should include nickname and role"

@pytest.mark.asyncio
async def test_failed_login_attempts_increment(db_session: AsyncSession, user: User):
    """
    Tests that failed login attempts can be incremented and persisted correctly.
    """
    initial_attempts = user.failed_login_attempts
    user.failed_login_attempts += 1
    await db_session.commit()
    await db_session.refresh(user)
    assert user.failed_login_attempts == initial_attempts + 1, "Failed login attempts should increment"

@pytest.mark.asyncio
async def test_last_login_update(db_session: AsyncSession, user: User):
    """
    Tests updating the last login timestamp.
    """
    new_last_login = datetime.now(timezone.utc)
    user.last_login_at = new_last_login
    await db_session.commit()
    await db_session.refresh(user)
    assert user.last_login_at == new_last_login, "Last login timestamp should update correctly"

@pytest.mark.asyncio
async def test_account_lock_and_unlock(db_session: AsyncSession, user: User):
    """
    Tests locking and unlocking the user account.
    """
    # Initially, the account should not be locked.
    assert not user.is_locked, "Account should initially be unlocked"

    # Lock the account and verify.
    user.lock_account()
    await db_session.commit()
    await db_session.refresh(user)
    assert user.is_locked, "Account should be locked after calling lock_account()"

    # Unlock the account and verify.
    user.unlock_account()
    await db_session.commit()
    await db_session.refresh(user)
    assert not user.is_locked, "Account should be unlocked after calling unlock_account()"

@pytest.mark.asyncio
async def test_email_verification(db_session: AsyncSession, user: User):
    """
    Tests the email verification functionality.
    """
    # Initially, the email should not be verified.
    assert not user.email_verified, "Email should initially be unverified"

    # Verify the email and check.
    user.verify_email()
    await db_session.commit()
    await db_session.refresh(user)
    assert user.email_verified, "Email should be verified after calling verify_email()"

@pytest.mark.asyncio
async def test_user_profile_pic_url_update(db_session: AsyncSession, user: User):
    """
    Tests the profile pic update functionality.
    """
    # Initially, the profile pic should be updated.

    # Verify the email and check.
    profile_pic_url = "http://myprofile/picture.png"
    user.profile_picture_url = profile_pic_url
    await db_session.commit()
    await db_session.refresh(user)
    assert user.profile_picture_url == profile_pic_url, "The profile pic did not update"

@pytest.mark.asyncio
async def test_user_linkedin_url_update(db_session: AsyncSession, user: User):
    """
    Tests the profile pic update functionality.
    """
    # Initially, the linkedin should  be updated.

    # Verify the linkedin profile url.
    profile_linkedin_url = "http://www.linkedin.com/profile"
    user.linkedin_profile_url = profile_linkedin_url
    await db_session.commit()
    await db_session.refresh(user)
    assert user.linkedin_profile_url == profile_linkedin_url, "The profile pic did not update"


@pytest.mark.asyncio
async def test_user_github_url_update(db_session: AsyncSession, user: User):
    """
    Tests the profile pic update functionality.
    """
    # Initially, the linkedin should  be updated.

    # Verify the linkedin profile url.
    profile_github_url = "http://www.github.com/profile"
    user.github_profile_url = profile_github_url
    await db_session.commit()
    await db_session.refresh(user)
    assert user.github_profile_url == profile_github_url, "The github did not update"


@pytest.mark.asyncio
async def test_update_user_role(db_session: AsyncSession, user: User):
    """
    Tests updating the user's role and ensuring it persists correctly.
    """
    user.role = UserRole.ADMIN
    await db_session.commit()
    await db_session.refresh(user)
    assert user.role == UserRole.ADMIN, "Role update should persist correctly in the database"

@pytest.mark.asyncio
async def test_update_user_bio_field(db_session, user):
    new_bio = "Cybersecurity enthusiast with 5 years of experience."
    updated_user = await UserService.update(db_session, user.id, {"bio": new_bio})
    assert updated_user is not None
    assert updated_user.bio == new_bio

@pytest.mark.asyncio
async def test_update_user_location(db_session, user):
    new_location = "New Jersey, USA"
    updated_user = await UserService.update(db_session, user.id, {"location": new_location})
    assert updated_user is not None
    assert updated_user.location == new_location

@pytest.mark.asyncio
async def test_update_multiple_profile_fields(db_session, user):
    data = {
        "first_name": "Alice",
        "last_name": "Walker",
        "linkedin_profile_url": "https://linkedin.com/in/alicewalker"
    }
    updated_user = await UserService.update(db_session, user.id, data)
    assert updated_user.first_name == "Alice"
    assert updated_user.last_name == "Walker"
    assert updated_user.linkedin_profile_url == data["linkedin_profile_url"]

@pytest.mark.asyncio
async def test_update_profile_with_invalid_url(db_session, user):
    invalid_url = "htp:/not.a.valid.url"
    updated_user = await UserService.update(db_session, user.id, {"github_profile_url": invalid_url})
    assert updated_user is None

@pytest.mark.asyncio
async def test_upgrade_user_to_professional(db_session, user):
    updated_user = await UserService.update(db_session, user.id, {"is_professional": True})
    assert updated_user.is_professional is True
    assert isinstance(updated_user.professional_status_updated_at, datetime)

@pytest.mark.asyncio
async def test_downgrade_user_from_professional(db_session, user):
    await UserService.update(db_session, user.id, {"is_professional": True})
    updated_user = await UserService.update(db_session, user.id, {"is_professional": False})
    assert updated_user.is_professional is False

@pytest.mark.asyncio
async def test_update_user_empty_data(db_session, user):
    updated_user = await UserService.update(db_session, user.id, {})
    assert updated_user is None

@pytest.mark.asyncio
async def test_update_user_password_and_login(db_session, verified_user):
    new_password = "SecureNewPass!99"
    # Use update_profile to avoid schema validation issues
    updated_user = await UserService.update_profile(db_session, verified_user.id, {"password": new_password})
    assert updated_user is not None, "User should be updated successfully"

    # Now test login with the new password
    logged_in_user = await UserService.login_user(db_session, verified_user.email, new_password)
    assert logged_in_user is not None, "User should be able to login with new password"


@pytest.mark.asyncio
async def test_update_profile_picture_url(db_session, user):
    url = "https://example.com/profile-pic.png"
    updated_user = await UserService.update(db_session, user.id, {"profile_picture_url": url})
    assert updated_user.profile_picture_url == url

@pytest.mark.asyncio
async def test_update_user_role_directly(db_session, user):
    updated_user = await UserService.update(db_session, user.id, {"role": UserRole.MANAGER})
    assert updated_user.role == UserRole.MANAGER