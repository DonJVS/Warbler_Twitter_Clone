"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User


os.environ['DATABASE_URL'] = "postgresql:///warbler_test"



from app import app, CURR_USER_KEY


db.create_all()


app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)

        db.session.commit()

    def tearDown(self):
        """Clean up any fouled transaction."""
        db.session.rollback()
        db.drop_all()
        db.create_all()

    def test_add_message(self):
        """Can use add a message?"""



        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id


            resp = c.post("/messages/new", data={"text": "Hello"})

            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")

    def test_view_message(self):
        """Can user view a message?"""

        msg = Message(
            text="Test message",
            user_id=self.testuser.id
        )

        db.session.add(msg)
        db.session.commit()

        with self.client as c:
            resp = c.get(f"/messages/{msg.id}")
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Test message", str(resp.data))

    def test_delete_message(self):
        """Can user delete their own message?"""

        msg = Message(
            text="Test message",
            user_id=self.testuser.id
        )

        db.session.add(msg)
        db.session.commit()

        msg = Message.query.get(msg.id)

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post(f"/messages/{msg.id}/delete", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            msg = Message.query.get(msg.id)
            self.assertIsNone(msg)

    def test_unauthorized_delete_message(self):
        """Is user prevented from deleting another user's message?"""

        other_user = User.signup(username="otheruser",
                                 email="other@test.com",
                                 password="otheruser",
                                 image_url=None)

        db.session.commit()

        msg = Message(
            text="Test message",
            user_id=self.testuser.id
        )

        db.session.add(msg)
        db.session.commit()

        msg = Message.query.get(msg.id)

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = other_user.id

            resp = c.post(f"/messages/{msg.id}/delete", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

            msg = Message.query.get(msg.id)
            self.assertIsNotNone(msg)

    def test_view_messages_without_logging_in(self):
        """Can messages be viewed without logging in?"""

        msg = Message(
            text="Test message",
            user_id=self.testuser.id
        )

        db.session.add(msg)
        db.session.commit()

        with self.client as c:
            resp = c.get(f"/messages/{msg.id}")
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Test message", str(resp.data))

    def test_add_message_without_logging_in(self):
        """Is user prevented from adding a message without logging in?"""

        with self.client as c:
            resp = c.post("/messages/new", data={"text": "Hello"}, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

            msg = Message.query.filter_by(text="Hello").first()
            self.assertIsNone(msg)

if __name__ == '__main__':
    import unittest
    unittest.main()
