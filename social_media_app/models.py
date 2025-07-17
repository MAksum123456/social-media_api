import pathlib
import uuid

from django.db import models

from social_media_api import settings


def image_path(instance, filename: str) -> str:
    filename = f"{instance.id}-{uuid.uuid4()}" + pathlib.Path(filename).suffix
    return str(pathlib.Path("uploads/media") / pathlib.Path(filename))


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    username = models.CharField(max_length=255, unique=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    date_of_birth = models.DateField(blank=True, null=True)
    bio = models.TextField(max_length=1000, blank=True, null=True)
    profile_picture = models.ImageField(null=True, upload_to=image_path)
    profile_followers = models.ManyToManyField(
        "self", through="Follow", symmetrical=False
    )

    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self) -> str:
        return f"{self.username} ({self.full_name()})"

    class Meta:
        ordering = ["username"]


class Post(models.Model):
    title = models.CharField(max_length=255)
    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="posts"
    )
    content = models.TextField(max_length=1000, blank=True, null=True)
    media = models.FileField(null=True, upload_to=image_path)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title}: {self.content}"


class Comment(models.Model):
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name="post_comments"
    )
    content = models.TextField(max_length=1000)
    commentator = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="commentator_comments",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.content[:30] + ("..." if len(self.content) > 30 else "")


class Follow(models.Model):
    follower = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="following"
    )
    following = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="followers"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("follower", "following")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.follower} follows {self.following}"


class Like(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="likes"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "post")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} liked {self.post}"
