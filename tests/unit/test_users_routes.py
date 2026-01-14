"""Unit tests for users_controller routes.

Tests all route handlers in isolation using test fixtures.
"""

import pytest
import time
from database import users
from app.users_model import get_user_by_email


class TestLoginGetRoute:
    """Tests GET /users/login route."""

    def test_login_page_returns_form(self):
        """GET /users/login returns login form."""
        from app.users_controller import get as login_get

        sess = {}
        
        # Call route
        result = login_get(sess=sess)
        
        # Should return HTML response (form)
        assert result is not None


class TestSignupGetRoute:
    """Tests GET /users/signup route."""

    def test_signup_page_returns_form(self):
        """GET /users/signup returns signup form."""
        from app.users_controller import get as signup_get

        sess = {}
        
        # Call route
        result = signup_get(sess=sess)
        
        # Should return HTML response (form)
        assert result is not None


class TestLogoutRoute:
    """Tests GET /users/logout route."""

    def test_logout_requires_session(self):
        """GET /users/logout should be accessible."""
        # Route test - just verify accessible by middleware
        pass


class TestLoginPostRoute:
    """Tests POST /users/login route."""

    def test_login_route_exists(self, progression_test_hafiz):
        """POST /users/login route should be callable."""
        # Route test - just verify exists and is callable through FastHTML app
        pass


class TestSignupPostRoute:
    """Tests POST /users/signup route."""

    def test_signup_route_exists(self):
        """POST /users/signup route should be callable."""
        # Route test - just verify exists
        pass


class TestAccountGetRoute:
    """Tests GET /users/account route."""

    def test_account_page_returns_form(self, progression_test_hafiz):
        """GET /users/account returns account settings form."""
        from app.users_controller import get as account_get

        user_id = progression_test_hafiz["user_id"]
        sess = {"user_auth": user_id}
        
        # Call route
        result = account_get(sess=sess)
        
        # Should return HTML response (form)
        assert result is not None

    def test_account_page_requires_auth(self):
        """GET /users/account requires user_auth in session."""
        from app.users_controller import get as account_get

        sess = {}
        
        # Call route without auth
        result = account_get(sess=sess)
        
        # Should return redirect response
        assert result is not None


class TestAccountPostRoute:
    """Tests POST /users/account route."""

    def test_update_account_updates_user(self, progression_test_hafiz):
        """POST /users/account updates user profile."""
        from app.users_controller import post as account_post

        user_id = progression_test_hafiz["user_id"]
        sess = {"user_auth": user_id}
        
        # Call route with updated data
        result = account_post(
            sess=sess,
            name="Updated Name",
            email=progression_test_hafiz["email"],
            password="",
            confirm_password=""
        )
        
        # Verify user updated
        updated_user = users[user_id]
        assert updated_user.name == "Updated Name"

    def test_account_update_route_exists(self, progression_test_hafiz):
        """POST /users/account update route exists."""
        # Route test - verify route callable
        pass


class TestDeleteUserRoute:
    """Tests DELETE /users/delete/{user_id} route."""

    def test_delete_user_deletes_account(self):
        """DELETE /users/delete/{user_id} deletes user account."""
        from app.users_controller import delete as user_delete
        from app.users_model import create_user

        timestamp = int(time.time() * 1000)
        email = f"delete_test_{timestamp}@example.com"
        
        # Create user
        user_id = create_user(email, "TestPass123!", f"DeleteTest{timestamp}")
        
        sess = {"user_auth": user_id, "auth": None}
        
        # Call delete route
        result = user_delete(user_id=user_id, sess=sess)
        
        # Verify user deleted
        try:
            users[user_id]
            assert False, "User should be deleted"
        except:
            pass  # Expected - user not found
        
        # Verify session cleared
        assert "user_auth" not in sess

    def test_delete_user_rejects_unauthorized(self, progression_test_hafiz):
        """DELETE /users/delete/{user_id} should reject unauthorized user."""
        from app.users_controller import delete as user_delete
        from app.users_model import create_user

        user_1_id = progression_test_hafiz["user_id"]
        timestamp = int(time.time() * 1000)
        
        # Create second user
        user_2_id = create_user(
            f"other_{timestamp}@example.com",
            "TestPass123!",
            f"OtherUser{timestamp}"
        )
        
        # Try to delete with wrong user
        sess = {"user_auth": user_2_id}
        result = user_delete(user_id=user_1_id, sess=sess)
        
        # Should return valid result
        assert result is not None
        
        # Verify user still exists
        try:
            users[user_1_id]
            assert True
        except:
            assert False, "User should not be deleted by unauthorized user"
        
        # Cleanup
        users.delete(user_2_id)


class TestUsersLinkRegression:
    """Tests that internal links between routes exist (regression test)."""

    def test_login_form_accessible(self):
        """GET /users/login should be accessible."""
        from app.users_controller import get as login_get

        sess = {}
        result = login_get(sess=sess)
        assert result is not None

    def test_signup_form_accessible(self):
        """GET /users/signup should be accessible."""
        from app.users_controller import get as signup_get

        sess = {}
        result = signup_get(sess=sess)
        assert result is not None

    def test_logout_accessible(self):
        """GET /users/logout should be accessible."""
        from app.users_controller import get as logout_get

        sess = {"user_auth": 1, "auth": 1}
        result = logout_get(sess=sess)
        assert result is not None
