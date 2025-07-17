from django.urls import path, include
from rest_framework import routers

from social_media_app.views import (
    ProfileViewSet,
    PostViewSet,
    CommentViewSet,
    FollowView,
    UnfollowView, LikeViewSet,
)

app_name = "social_media_app"

router = routers.DefaultRouter()
router.register("profile", ProfileViewSet)
router.register("post", PostViewSet)
router.register("comment", CommentViewSet)
router.register("like", LikeViewSet, basename="like")


urlpatterns = [
    path("", include(router.urls)),
    path("follow/", FollowView.as_view(), name="follow"),
    path("unfollow/", UnfollowView.as_view(), name="unfollow"),
]
