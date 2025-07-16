from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.exceptions import ValidationError
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory
from social_media_app.models import Profile, Post, Comment, Follow, Like
from social_media_app.serializers import (
    ProfileMiniSerializer,
    ProfileSerializer,
    ProfileRetrieveSerializer,
    ProfileCreateSerializer,
    PostSerializer,
    PostCreateSerializer,
    CommentSerializer,
    CommentCreateSerializer,
    CommentRetrieveSerializer,
    CommentUpdateSerializer,
    FollowingSerializer,
    FollowerSerializer,
    FollowActionSerializer,
    UnfollowActionSerializer,
    LikeSerializer,
    CreateLikeSerializer,
)

User = get_user_model()


class SerializersTestBase(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user1 = User.objects.create_user(
            email="user1@gmail.com", password="pass123"
        )
        self.user2 = User.objects.create_user(
            email="user2@gmail.com", password="pass123"
        )
        self.user3 = User.objects.create_user(
            email="user3@gmail.com", password="pass123"
        )

        self.profile1 = Profile.objects.create(
            user=self.user1, username="profile1", first_name="John", last_name="Doe"
        )
        self.profile2 = Profile.objects.create(
            user=self.user2, username="profile2", first_name="Jane", last_name="Smith"
        )

        self.post = Post.objects.create(
            title="Test Post", profile=self.profile1, content="Test content"
        )

        self.comment = Comment.objects.create(
            post=self.post, commentator=self.profile2, content="Test comment"
        )

        self.follow = Follow.objects.create(
            follower=self.profile1, following=self.profile2
        )

        self.like = Like.objects.create(user=self.user1, post=self.post)


class ProfileSerializersTests(SerializersTestBase):
    def test_profile_mini_serializer(self):
        serializer = ProfileMiniSerializer(instance=self.profile1)
        self.assertEqual(serializer.data, {"username": "profile1"})

    def test_profile_serializer(self):
        serializer = ProfileSerializer(instance=self.profile1)
        expected_fields = {
            "id",
            "username",
            "first_name",
            "last_name",
            "profile_picture",
        }
        self.assertEqual(set(serializer.data.keys()), expected_fields)

    def test_profile_retrieve_serializer(self):
        self.profile1.followers_count = 1
        self.profile1.following_count = 1

        serializer = ProfileRetrieveSerializer(instance=self.profile1)
        data = serializer.data

        self.assertEqual(data["followers"], 1)
        self.assertEqual(data["following"], 1)
        self.assertEqual(len(data["posts"]), 1)
        self.assertEqual(data["posts"][0]["title"], "Test Post")

    def test_profile_create_serializer(self):
        data = {"username": "newprofile", "first_name": "New", "last_name": "User"}
        request = self.factory.post("/")
        request.user = self.user3

        serializer = ProfileCreateSerializer(data=data, context={"request": request})
        self.assertTrue(serializer.is_valid())

        profile = serializer.save()
        self.assertEqual(profile.user, self.user3)
        self.assertEqual(profile.username, "newprofile")


class PostSerializersTests(SerializersTestBase):
    def test_post_serializer(self):
        serializer = PostSerializer(instance=self.post)
        data = serializer.data

        self.assertEqual(data["title"], "Test Post")
        self.assertEqual(data["likes_count"], 1)
        self.assertEqual(data["profile"]["username"], "profile1")

    def test_post_create_serializer(self):
        data = {
            "title": "New Post",
            "content": "New content",
            "media": SimpleUploadedFile("test.jpg", b"file_content"),
        }
        request = self.factory.post("/")
        request.user = self.user1

        serializer = PostCreateSerializer(data=data, context={"request": request})
        self.assertTrue(serializer.is_valid())

        post = serializer.save()
        self.assertEqual(post.profile, self.profile1)
        self.assertEqual(post.title, "New Post")


class CommentSerializersTests(SerializersTestBase):
    def test_comment_serializer(self):
        serializer = CommentSerializer(instance=self.comment)
        data = serializer.data

        self.assertEqual(data["content"], "Test comment")
        self.assertEqual(data["post"], self.post.id)
        self.assertEqual(data["commentator"], self.profile2.id)

    def test_comment_create_serializer(self):
        data = {"post": self.post.id, "content": "New comment"}
        request = self.factory.post("/")
        request.user = self.user2

        serializer = CommentCreateSerializer(data=data, context={"request": request})
        self.assertTrue(serializer.is_valid())

        comment = serializer.save()
        self.assertEqual(comment.commentator, self.profile2)
        self.assertEqual(comment.content, "New comment")

    def test_comment_retrieve_serializer(self):
        serializer = CommentRetrieveSerializer(instance=self.comment)
        data = serializer.data

        self.assertEqual(data["content"], "Test comment")
        self.assertEqual(data["post"]["title"], "Test Post")
        self.assertEqual(data["commentator"]["username"], "profile2")

    def test_comment_update_serializer(self):
        data = {"content": "Updated content"}
        serializer = CommentUpdateSerializer(instance=self.comment, data=data)
        self.assertTrue(serializer.is_valid())

        comment = serializer.save()
        self.assertEqual(comment.content, "Updated content")


class FollowSerializersTests(SerializersTestBase):

    def test_follower_serializer(self):
        follow_reverse = Follow.objects.create(
            follower=self.profile2, following=self.profile1
        )
        serializer = FollowerSerializer(instance=follow_reverse)
        data = serializer.data

        self.assertEqual(data["username"], "profile2")
        self.assertEqual(data["full_name"], "Jane Smith")

    def test_follow_action_serializer(self):
        request = self.factory.post("/")
        request.user = self.user1

        serializer = FollowActionSerializer(
            data={"profile": "profile2"}, context={"request": request}
        )
        self.assertFalse(serializer.is_valid())

        profile3 = Profile.objects.create(
            user=self.user3, username="profile3", first_name="Test", last_name="User"
        )
        serializer = FollowActionSerializer(
            data={"profile": "profile3"}, context={"request": request}
        )
        self.assertTrue(serializer.is_valid())

    def test_unfollow_action_serializer(self):
        request = self.factory.post("/")
        request.user = self.user1

        serializer = UnfollowActionSerializer(
            data={"profile": "profile2"}, context={"request": request}
        )
        self.assertTrue(serializer.is_valid())

        # Test invalid unfollow
        serializer = UnfollowActionSerializer(
            data={"profile": "profile1"}, context={"request": request}
        )
        self.assertFalse(serializer.is_valid())


class LikeSerializersTests(SerializersTestBase):
    def test_like_serializer(self):
        serializer = LikeSerializer(instance=self.like)
        data = serializer.data

        self.assertEqual(data["post"]["title"], "Test Post")

    def test_create_like_serializer(self):
        data = {"post": self.post.id}
        request = self.factory.post("/")
        request.user = self.user2

        serializer = CreateLikeSerializer(data=data, context={"request": request})
        self.assertTrue(serializer.is_valid())

        like = serializer.save()
        self.assertEqual(like.user, self.user2)
        self.assertEqual(like.post, self.post)
