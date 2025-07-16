from django.contrib import admin
from social_media_app.models import (
    Profile,
    Post,
    Comment,
    Follow,
    Like
)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ["first_name", "last_name", "date_of_birth", "bio"]
    search_fields = ["first_name", "last_name"]


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ["title", "profile", "content", "created_at"]
    search_fields = ["title", "content"]


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ["post", "content", "commentator", "created_at"]
    search_fields = ["post", "content", "commentator"]


admin.site.register(Follow)
admin.site.register(Like)
