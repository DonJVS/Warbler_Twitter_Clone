"""User model tests."""


import os
from unittest import TestCase
from sqlalchemy.exc import IntegrityError

from models import db, User, Message, Follows


os.environ['DATABASE_URL'] = "postgresql:///warbler_test"



from app import app

db.create_all()


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        self.client = app.test_client()

        self.user1 = User.signup("testuser1", "test1@test.com", "password", None)
        self.user2 = User.signup("testuser2", "test2@test.com", "password", None)
        db.session.commit()

    def tearDown(self):
        """Clean up any fouled transaction."""
        db.session.rollback()
        db.drop_all()
        db.create_all()

    def test_repr(self):
        """Does the repr method work as expected?"""
        self.assertEqual(repr(self.user1), "<User #1: testuser1, test1@test.com>")

    def test_is_following(self):
        """Does is_following successfully detect when user1 is following user2?"""
        self.user1.following.append(self.user2)
        db.session.commit()
        self.assertTrue(self.user1.is_following(self.user2))
        self.assertFalse(self.user2.is_following(self.user1))

    def test_is_not_following(self):
        """Does is_following successfully detect when user1 is not following user2?"""
        self.assertFalse(self.user1.is_following(self.user2))

    def test_is_followed_by(self):
        """Does is_followed_by successfully detect when user1 is followed by user2?"""
        self.user2.following.append(self.user1)
        db.session.commit()
        self.assertTrue(self.user1.is_followed_by(self.user2))
        self.assertFalse(self.user2.is_followed_by(self.user1))

    def test_is_not_followed_by(self):
        """Does is_followed_by successfully detect when user1 is not followed by user2?"""
        self.assertFalse(self.user1.is_followed_by(self.user2))

    def test_signup(self):
        """Does User.signup successfully create a new user given valid credentials?"""
        user = User.signup("testuser3", "test3@test.com", "password", None)
        db.session.commit()
        self.assertIsNotNone(user)
        self.assertEqual(user.username, "testuser3")
        self.assertEqual(user.email, "test3@test.com")
        self.assertTrue(user.password.startswith("$2b$"))

    def test_signup_fail(self):
        """Does User.signup fail to create a new user if any of the validations fail?"""
        invalid_user = User.signup(None, "test@test.com", "password", None)
        with self.assertRaises(IntegrityError):
            db.session.commit()
        db.session.rollback()

        invalid_user = User.signup("testuser4", None, "password", None)
        with self.assertRaises(IntegrityError):
            db.session.commit()
        db.session.rollback()

    def test_authenticate(self):
        """Does User.authenticate successfully return a user given a valid username and password?"""
        user = User.authenticate("testuser1", "password")
        self.assertIsNotNone(user)
        self.assertEqual(user.username, "testuser1")

    def test_authenticate_invalid_username(self):
        """Does User.authenticate fail to return a user when the username is invalid?"""
        self.assertFalse(User.authenticate("wrongusername", "password"))

    def test_authenticate_invalid_password(self):
        """Does User.authenticate fail to return a user when the password is invalid?"""
        self.assertFalse(User.authenticate("testuser1", "wrongpassword"))

if __name__ == '__main__':
    import unittest
    unittest.main()