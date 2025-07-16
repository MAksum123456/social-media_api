from django.contrib.auth import get_user_model
from rest_framework import serializers

from social_media_app.models import Profile, Post, Comment, Follow, Like

User = get_user_model()


class ProfileMiniSerializer(serializers.ModelSerializer):

    class Meta:
        model = Profile
        fields = ("username",)


class PostSerializer(serializers.ModelSerializer):
    likes_count = serializers.IntegerField(
        source="likes.count",
        read_only=True
    )
    profile = ProfileMiniSerializer(read_only=True)

    class Meta:
        model = Post
        fields = (
            "id",
            "title",
            "profile",
            "content",
            "media",
            "likes_count",
            "created_at",
        )


class PostCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Post
        fields = ("title", "content", "media")

    def create(self, validated_data):
        profile = self.context["request"].user.profile

        post = Post.objects.create(
            title=validated_data["title"],
            content=validated_data["content"],
            media=validated_data["media"],
            profile=profile,
        )
        return post


class ProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = Profile
        fields = (
            "id",
            "username",
            "first_name",
            "last_name",
            "profile_picture",
        )


class ProfileRetrieveSerializer(serializers.ModelSerializer):
    followers = serializers.SerializerMethodField()
    following = serializers.SerializerMethodField()
    posts = PostSerializer(many=True, read_only=True)

    class Meta:
        model = Profile
        fields = (
            "username",
            "first_name",
            "last_name",
            "date_of_birth",
            "bio",
            "profile_picture",
            "followers",
            "following",
            "posts",
        )

    def get_followers(self, obj) -> int:
        return getattr(obj, "followers_count")

    def get_following(self, obj) -> int:
        return getattr(obj, "following_count")


class ProfileCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Profile
        fields = (
            "username",
            "first_name",
            "last_name",
            "date_of_birth",
            "bio",
            "profile_picture",
        )

    def create(self, validated_data):
        if "user" not in validated_data:
            validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class CommentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Comment
        fields = (
            "id",
            "post",
            "content",
            "commentator",
            "created_at",
        )


class CommentCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Comment
        fields = (
            "post",
            "content",
        )

    def create(self, validated_data):
        profile = self.context["request"].user.profile

        comment = Comment.objects.create(
            commentator=profile,
            post=validated_data["post"],
            content=validated_data["content"],
        )

        return comment


class CommentUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Comment
        fields = ("content",)


class CommentRetrieveSerializer(serializers.ModelSerializer):
    post = PostSerializer(read_only=True)
    commentator = ProfileSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = (
            "id",
            "post",
            "content",
            "commentator",
            "created_at",
        )


class FollowingSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    profile_picture = serializers.SerializerMethodField()

    class Meta:
        model = Follow
        fields = ("username", "full_name")

    def get_username(self, obj):
        return obj.following.username

    def get_full_name(self, obj):
        return f"{obj.following.first_name} {obj.following.last_name}"

    def get_profile_picture(self, obj):
        return (
            obj.following.profile_picture
            if obj.following.profile_picture else None
        )


class FollowerSerializer(FollowingSerializer):

    def get_username(self, obj):
        return obj.follower.username

    def get_full_name(self, obj):
        return f"{obj.follower.first_name} {obj.follower.last_name}"

    def get_profile_picture(self, obj):
        return (
            obj.follower.profile_picture.url
            if obj.follower.profile_picture else None
        )


class FollowActionSerializer(serializers.Serializer):
    profile = serializers.SlugRelatedField(
        slug_field="username", queryset=Profile.objects.none()
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        user = self.context["request"].user
        if user and user.is_authenticated:
            me = user.profile
            to_follow = Profile.objects.exclude(
                followers__follower=me
            ).exclude(pk=me.pk)
            self.fields["profile"].queryset = to_follow

    def validate_profile(self, value):
        me = self.context["request"].user.profile
        if Follow.objects.filter(follower=me, following=value).exists():
            raise serializers.ValidationError("Already following.")
        return value


class UnfollowActionSerializer(serializers.Serializer):
    profile = serializers.SlugRelatedField(
        slug_field="username", queryset=Profile.objects.none()
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        user = self.context["request"].user
        if user and user.is_authenticated:
            me = user.profile
            to_unfollow = Profile.objects.filter(
                followers__follower=me
            ).exclude(pk=me.pk)
            self.fields["profile"].queryset = to_unfollow

    def validate_profile(self, value):
        me = self.context["request"].user.profile
        if not Follow.objects.filter(follower=me, following=value).exists():
            raise serializers.ValidationError("Not following.")
        return value


class LikeSerializer(serializers.ModelSerializer):
    post = PostSerializer(read_only=True)

    class Meta:
        model = Like
        fields = ("id", "post")


class CreateLikeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Like
        fields = ("id", "post")

    def create(self, validated_data):
        user = self.context["request"].user

        like = Like.objects.create(
            post=validated_data["post"],
            user=user,
        )
        return like
