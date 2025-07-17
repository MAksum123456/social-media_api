from django.db.models import Count
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    extend_schema_view
)

from rest_framework import viewsets, generics, status
from .mixins import UploadImageMixin

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from social_media_app.models import Profile, Post, Comment, Follow, Like
from social_media_app.permission import (
    IsProfileOwnerOrReadOnly,
    IsCommentOwnerOrReadOnly,
    IsPostOwnerOrReadOnly,
)
from social_media_app.serializers import (
    ProfileSerializer,
    ProfileRetrieveSerializer,
    ProfileCreateSerializer,
    PostSerializer,
    CommentSerializer,
    CommentCreateSerializer,
    CommentRetrieveSerializer,
    FollowActionSerializer,
    UnfollowActionSerializer,
    PostCreateSerializer,
    CommentUpdateSerializer,
    LikeSerializer,
    CreateLikeSerializer,
)


@extend_schema_view(
    list=extend_schema(
        tags=["Profile"],
        description="List profile with optional filters:"
                    " username, first_name, and last_name",
        parameters=[
            OpenApiParameter(
                name="username",
                type=OpenApiTypes.STR,
                required=False,
                description="Filter by username",
            ),
            OpenApiParameter(
                name="first_name",
                type=OpenApiTypes.STR,
                required=False,
                description="Filter by first name",
            ),
            OpenApiParameter(
                name="last_name",
                type=OpenApiTypes.STR,
                required=False,
                description="Filter by last name",
            ),
        ],
    )
)
class ProfileViewSet(UploadImageMixin, viewsets.ModelViewSet):
    queryset = Profile.objects.select_related("user").annotate(
        followers_count=Count("followers", distinct=True),
        following_count=Count("following", distinct=True),
    )
    permission_classes = [IsProfileOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["username", "first_name", "last_name"]

    def get_serializer_class(self):
        if self.action == "list":
            return ProfileSerializer
        if self.action == "retrieve":
            return ProfileRetrieveSerializer
        if self.action in ("create", "update"):
            return ProfileCreateSerializer
        return ProfileSerializer


@extend_schema_view(
    list=extend_schema(
        tags=["Post"],
        description="List post with optional filters: title, profile_id",
        parameters=[
            OpenApiParameter(
                name="title",
                type=OpenApiTypes.STR,
                required=False,
                description="Filter by title",
            ),
            OpenApiParameter(
                name="profile_id",
                type=OpenApiTypes.INT,
                required=False,
                description="Filter by profile_id",
            ),
        ],
    )
)
class PostViewSet(UploadImageMixin, viewsets.ModelViewSet):
    queryset = (
        Post.objects.select_related("profile", "profile__user")
        .prefetch_related("likes")
        .annotate(
            likes_count=Count("likes"),
        )
    )
    serializer_class = PostSerializer
    permission_classes = [IsPostOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["title", "profile_id"]

    def get_serializer_class(self):
        if self.action == "list":
            return PostSerializer
        if self.action in ("create", "update"):
            return PostCreateSerializer
        return PostSerializer


@extend_schema(
    tags=["Comment"],
    description="returns all comments, you can add your "
    "own comment to the post, or delete your "
    "own comment",
)
class CommentViewSet(viewsets.ModelViewSet):

    queryset = Comment.objects.select_related(
        "post", "commentator", "commentator__user"
    )
    permission_classes = [IsCommentOwnerOrReadOnly]

    def get_serializer_class(self):
        if self.action == "list":
            return CommentSerializer
        if self.action == "create":
            return CommentCreateSerializer
        if self.action == "update":
            return CommentUpdateSerializer
        if self.action == "retrieve":
            return CommentRetrieveSerializer
        return CommentSerializer


@extend_schema(
    tags=["Follow"],
    description="here you can subscribe to users, only those users "
    "to whom you have not yet subscribed are displayed",
)
class FollowView(generics.CreateAPIView):

    serializer_class = FollowActionSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        me = request.user.profile
        serializer = self.get_serializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        target = serializer.validated_data["profile"]
        follow, created = Follow.objects.get_or_create(
            follower=me,
            following=target
        )
        return Response(
            {"following": target.username, "created": created},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


@extend_schema(
    tags=["UnFollow"],
    description="here you can unsubscribe from users, "
    "only those users to whom you are subscribed are displayed",
)
class UnfollowView(generics.CreateAPIView):
    serializer_class = UnfollowActionSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        me = request.user.profile
        serializer = self.get_serializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        target = serializer.validated_data["profile"]
        Follow.objects.filter(follower=me, following=target).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    tags=["Like"],
    description="returns posts that have been liked by the user, "
    "you can also like a post or remove a like",
)
class LikeViewSet(viewsets.ModelViewSet):
    queryset = Like.objects.select_related("post", "user")
    serializer_class = LikeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Like.objects.filter(user=self.request.user)
            .select_related("post__profile")
            .prefetch_related("post__likes")
            .annotate(post_likes_count=Count("post__likes"))
        )

    def get_serializer_class(self):
        if self.action == "list":
            return LikeSerializer
        if self.action == "create":
            return CreateLikeSerializer
        return LikeSerializer
