"""User views tests."""

import os
from unittest import TestCase
from sqlalchemy.exc import IntegrityError
from models import db, User, Message, Likes, Follows


os.environ['DATABASE_URL'] = "postgresql:///warbler_test"

from app import app, CURR_USER_KEY


db.create_all()


app.config['WTF_CSRF_ENABLED'] = False


class UserViewTestCase(TestCase):
    """Test views for users."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        self.client = app.test_client()

        self.testuser1 = User.signup(username="testuser1",
                                    email="test1@test.com",
                                    password="password",
                                    image_url=None)

        self.testuser2 = User.signup(username="testuser2",
                                    email="test2@test.com",
                                    password="password",
                                    image_url=None)

        db.session.commit()

    def tearDown(self):
        """Clean up any fouled transaction."""
        db.session.rollback()
        db.drop_all()
        db.create_all()

    def test_list_users(self):
        """Can user view the users list?"""

        with self.client as c:
            resp = c.get("/users")
            self.assertEqual(resp.status_code, 200)
            self.assertIn("testuser1", str(resp.data))
            self.assertIn("testuser2", str(resp.data))

    def test_view_user_profile(self):
        """Can user view a user's profile?"""

        with self.client as c:
            resp = c.get(f"/users/{self.testuser1.id}")
            self.assertEqual(resp.status_code, 200)
            self.assertIn("testuser1", str(resp.data))

    def test_follow_user(self):
        """Can user follow another user?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser1.id

                testuser2 = User.query.get(self.testuser2.id) 

            resp = c.post(f"/users/follow/{self.testuser2.id}", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Unfollow", str(resp.data))

            follow = Follows.query.filter_by(user_being_followed_id=self.testuser2.id, user_following_id=self.testuser1.id).first()
            self.assertIsNotNone(follow)

    def test_unfollow_user(self):
        """Can user unfollow another user?"""

        follow = Follows(user_being_followed_id=self.testuser2.id, user_following_id=self.testuser1.id)
        db.session.add(follow)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser1.id
                testuser2 = User.query.get(self.testuser2.id)

            resp = c.post(f"/users/stop-following/{self.testuser2.id}", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Follow", str(resp.data))

            follow = Follows.query.filter_by(user_being_followed_id=self.testuser2.id, user_following_id=self.testuser1.id).first()
            self.assertIsNone(follow)

    def test_unauthorized_follow(self):
        """Is user prevented from following if not logged in?"""
        self.testuser1 = User.query.get(self.testuser1.id)
        self.testuser2 = User.query.get(self.testuser2.id)

        with self.client as c:
            resp = c.post(f"/users/follow/{self.testuser2.id}", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

            follow = Follows.query.filter_by(user_being_followed_id=self.testuser2.id, user_following_id=self.testuser1.id).first()
            self.assertIsNone(follow)

    def test_unauthorized_unfollow(self):
        """Is user prevented from unfollowing if not logged in?"""

        follow = Follows(user_being_followed_id=self.testuser2.id, user_following_id=self.testuser1.id)
        db.session.add(follow)
        db.session.commit()

        self.testuser1 = User.query.get(self.testuser1.id)
        self.testuser2 = User.query.get(self.testuser2.id)

        with self.client as c:
            resp = c.post(f"/users/stop-following/{self.testuser2.id}", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

            follow = Follows.query.filter_by(user_being_followed_id=self.testuser2.id, user_following_id=self.testuser1.id).first()
            self.assertIsNotNone(follow)


class AuthViewTestCase(TestCase):
    """Test views for authorization and authentication."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        self.client = app.test_client()

        self.testuser1 = User.signup(username="testuser1",
                                    email="test1@test.com",
                                    password="password",
                                    image_url=None)

        self.testuser2 = User.signup(username="testuser2",
                                    email="test2@test.com",
                                    password="password",
                                    image_url=None)

        db.session.commit()

    def tearDown(self):
        """Clean up any fouled transaction."""
        db.session.rollback()
        db.drop_all()
        db.create_all()

    def test_view_followers_logged_in(self):
        """When you're logged in, can you see the follower/following pages for any user?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser1.id
                self.testuser2 = User.query.get(self.testuser2.id)

            resp = c.get(f"/users/{self.testuser2.id}/followers")
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Followers", str(resp.data))

            resp = c.get(f"/users/{self.testuser2.id}/following")
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Following", str(resp.data))

    def test_view_followers_logged_out(self):
        """When you're logged out, are you disallowed from visiting a user's follower/following pages?"""

        with self.client as c:
            resp = c.get(f"/users/{self.testuser2.id}/followers", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

            resp = c.get(f"/users/{self.testuser2.id}/following", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

    def test_add_message_logged_in(self):
        """When you're logged in, can you add a message as yourself?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser1.id

            resp = c.post("/messages/new", data={"text": "Hello"}, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Hello", str(resp.data))

            msg = Message.query.filter_by(text="Hello").first()
            self.assertIsNotNone(msg)
            self.assertEqual(msg.user_id, self.testuser1.id)

    def test_delete_message_logged_in(self):
        """When you're logged in, can you delete a message as yourself?"""

        msg = Message(text="Test message", user_id=self.testuser1.id)
        db.session.add(msg)
        db.session.commit()

        msg = Message.query.get(msg.id)

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser1.id

            resp = c.post(f"/messages/{msg.id}/delete", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            msg = Message.query.get(msg.id)
            self.assertIsNone(msg)

    def test_add_message_logged_out(self):
        """When you're logged out, are you prohibited from adding messages?"""

        with self.client as c:
            resp = c.post("/messages/new", data={"text": "Hello"}, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

            msg = Message.query.filter_by(text="Hello").first()
            self.assertIsNone(msg)

    def test_delete_message_logged_out(self):
        """When you're logged out, are you prohibited from deleting messages?"""

        msg = Message(text="Test message", user_id=self.testuser1.id)
        db.session.add(msg)
        db.session.commit()

        msg = Message.query.get(msg.id)

        with self.client as c:
            resp = c.post(f"/messages/{msg.id}/delete", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

            msg = Message.query.get(msg.id)
            self.assertIsNotNone(msg)

    def test_add_message_as_other_user(self):
        """When you're logged in, are you prohibited from adding a message as another user?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser1.id

            # Attempt to add a message as another user (testuser2)
            resp = c.post("/messages/new", data={"text": "Hello"}, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Hello", str(resp.data))

            msg = Message.query.filter_by(text="Hello").first()
            self.assertIsNotNone(msg)
            self.assertEqual(msg.user_id, self.testuser1.id)

    def test_delete_message_as_other_user(self):
        """When you're logged in, are you prohibited from deleting a message as another user?"""

        msg = Message(text="Test message", user_id=self.testuser2.id)
        db.session.add(msg)
        db.session.commit()

        msg = Message.query.get(msg.id)

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser1.id

            resp = c.post(f"/messages/{msg.id}/delete", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

            msg = Message.query.get(msg.id)
            self.assertIsNotNone(msg)

if __name__ == '__main__':
    import unittest
    unittest.main()