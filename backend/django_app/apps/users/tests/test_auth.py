"""
Auth endpoint tests for the Django backend.
Tests registration, login, invalid credentials, and duplicate registration.

Run with:
    cd backend/django_app
    python manage.py test apps.users.tests.test_auth --verbosity=2
"""
import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

REGISTER_URL = '/api/v1/users/register/'
TOKEN_URL = '/api/v1/users/token/'
ME_URL = '/api/v1/users/me/'


class RegistrationTests(TestCase):
    """Tests for POST /api/v1/users/register/"""

    def setUp(self):
        self.client = Client()
        self.valid_payload = {
            'email': 'new@example.com',
            'password': 'securePass99!',
            'first_name': 'Jane',
            'last_name': 'Doe',
        }

    def test_register_success_returns_201(self):
        """Valid registration returns 201 and user data."""
        response = self.client.post(
            REGISTER_URL,
            data=json.dumps(self.valid_payload),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data['email'], self.valid_payload['email'])
        self.assertEqual(data['first_name'], 'Jane')
        # Password must never be returned
        self.assertNotIn('password', data)

    def test_register_creates_user_in_database(self):
        """Registered user exists in the database with hashed password."""
        self.client.post(
            REGISTER_URL,
            data=json.dumps(self.valid_payload),
            content_type='application/json',
        )
        user = User.objects.get(email=self.valid_payload['email'])
        self.assertTrue(user.check_password(self.valid_payload['password']))
        # Password must be hashed, not stored in plaintext
        self.assertNotEqual(user.password, self.valid_payload['password'])

    def test_register_duplicate_email_returns_400(self):
        """Registering with an already-used email returns 400."""
        # First registration
        self.client.post(
            REGISTER_URL,
            data=json.dumps(self.valid_payload),
            content_type='application/json',
        )
        # Second registration with same email
        response = self.client.post(
            REGISTER_URL,
            data=json.dumps(self.valid_payload),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)

    def test_register_missing_email_returns_400(self):
        """Registration without email returns 400."""
        payload = {**self.valid_payload}
        del payload['email']
        response = self.client.post(
            REGISTER_URL,
            data=json.dumps(payload),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)

    def test_register_missing_password_returns_400(self):
        """Registration without password returns 400."""
        payload = {**self.valid_payload}
        del payload['password']
        response = self.client.post(
            REGISTER_URL,
            data=json.dumps(payload),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)

    def test_register_rejects_get_method(self):
        """GET on register endpoint returns 405."""
        response = self.client.get(REGISTER_URL)
        self.assertEqual(response.status_code, 405)


class LoginTests(TestCase):
    """Tests for POST /api/v1/users/token/"""

    def setUp(self):
        self.client = Client()
        self.email = 'test@example.com'
        self.password = 'testPass99!'
        self.user = User.objects.create_user(
            email=self.email,
            password=self.password,
            first_name='Test',
            last_name='User',
        )

    def test_login_success_returns_tokens(self):
        """Valid credentials return access and refresh tokens."""
        response = self.client.post(
            TOKEN_URL,
            data=json.dumps({'email': self.email, 'password': self.password}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('access', data)
        self.assertIn('refresh', data)
        self.assertIsInstance(data['access'], str)
        self.assertIsInstance(data['refresh'], str)
        self.assertGreater(len(data['access']), 20)

    def test_login_wrong_password_returns_401(self):
        """Wrong password returns 401."""
        response = self.client.post(
            TOKEN_URL,
            data=json.dumps({'email': self.email, 'password': 'wrongpassword'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 401)

    def test_login_nonexistent_user_returns_401(self):
        """Login for a non-existent user returns 401."""
        response = self.client.post(
            TOKEN_URL,
            data=json.dumps({'email': 'nobody@example.com', 'password': 'irrelevant'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 401)

    def test_login_missing_password_returns_400(self):
        """Missing password field returns 400."""
        response = self.client.post(
            TOKEN_URL,
            data=json.dumps({'email': self.email}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)

    def test_login_empty_body_returns_400(self):
        """Empty body returns 400."""
        response = self.client.post(
            TOKEN_URL,
            data=json.dumps({}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)


class ProfileTests(TestCase):
    """Tests for GET /api/v1/users/me/ (requires JWT)."""

    def setUp(self):
        self.client = Client()
        self.email = 'me@example.com'
        self.password = 'profilePass99!'
        self.user = User.objects.create_user(
            email=self.email,
            password=self.password,
            first_name='Profile',
            last_name='User',
        )

    def _get_token(self):
        """Helper: obtain a valid access token."""
        response = self.client.post(
            TOKEN_URL,
            data=json.dumps({'email': self.email, 'password': self.password}),
            content_type='application/json',
        )
        return response.json()['access']

    def test_me_with_valid_token_returns_200(self):
        """Authenticated request to /me/ returns user data."""
        token = self._get_token()
        response = self.client.get(
            ME_URL,
            HTTP_AUTHORIZATION=f'Bearer {token}',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['email'], self.email)

    def test_me_without_token_returns_401(self):
        """/me/ without auth returns 401."""
        response = self.client.get(ME_URL)
        self.assertEqual(response.status_code, 401)
