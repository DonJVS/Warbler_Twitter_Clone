"""Message model tests."""

import os
from unittest import TestCase
from sqlalchemy.exc import IntegrityError
from models import db, User, Message, Likes
from app import app

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"


db.create_all()

class MessageModelTestCase(TestCase):
    """Test message model."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        self.client = app.test_client()

        self.user = User.signup("testuser", "test@test.com", "password", None)
        self.user_id = self.user.id
        db.session.commit()

        self.message = Message(
            text="This is a test message",
            user_id=self.user.id
        )

        db.session.add(self.message)
        db.session.commit()

    def tearDown(self):
        """Clean up any fouled transaction."""
        db.session.rollback()
        db.drop_all()
        db.create_all()

    def test_is_liked_by(self):
        """Does is_liked_by successfully detect when a message is liked by a user?"""
        like = Likes(user_id=self.user.id, message_id=self.message.id)
        db.session.add(like)
        db.session.commit()
        self.assertTrue(self.message.is_liked_by(self.user))

    def test_is_not_liked_by(self):
        """Does is_liked_by successfully detect when a message is not liked by a user?"""
        self.assertFalse(self.message.is_liked_by(self.user))

    def test_message_creation(self):
        """Does creating a message with valid data succeed?"""
        msg = Message(
            text="Another test message",
            user_id=self.user.id
        )
        db.session.add(msg)
        db.session.commit()
        self.assertIsNotNone(msg)
        self.assertEqual(msg.text, "Another test message")
        self.assertEqual(msg.user_id, self.user.id)

    def test_message_creation_fail(self):
        """Does creating a message fail if any of the validations fail?"""
        invalid_msg = Message(
            text=None,
            user_id=self.user.id
        )
        db.session.add(invalid_msg)
        with self.assertRaises(IntegrityError):
            db.session.commit()
        db.session.rollback()

        invalid_msg = Message(
            text="This message has no user",
            user_id=None
        )
        db.session.add(invalid_msg)
        with self.assertRaises(IntegrityError):
            db.session.commit()
        db.session.rollback() 
        
    def test_user_message_relationship(self):
        """Does the Message model properly associate with the User model?"""
        self.assertEqual(self.message.user_id, self.user.id)
        self.assertEqual(self.message.user.username, "testuser")

    def test_message_deletion_cascades(self):
        """Does deleting a Message also delete associated Likes?"""
        like = Likes(user_id=self.user.id, message_id=self.message.id)
        db.session.add(like)
        db.session.commit()
        self.assertTrue(Likes.query.filter_by(message_id=self.message.id).count() > 0)
        
        db.session.delete(self.message)
        db.session.commit()
        self.assertEqual(Likes.query.filter_by(message_id=self.message.id).count(), 0)

if __name__ == '__main__':
    import unittest
    unittest.main()