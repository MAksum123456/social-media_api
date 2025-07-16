from rest_framework import permissions


class IsProfileOwnerOrReadOnly(permissions.BasePermission):
    """
    Allows editing only by the profile owner; others have read-only access.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user


class IsCommentOwnerOrReadOnly(permissions.BasePermission):
    """
    Allows editing only by the comment owner; others have read-only access.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.commentator.user == request.user


class IsPostOwnerOrReadOnly(permissions.BasePermission):
    """
    Allows editing only by the post owner; others have read-only access.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.profile.user == request.user
