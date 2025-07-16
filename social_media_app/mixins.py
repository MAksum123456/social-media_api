from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated


class UploadImageMixin:
    @action(
        detail=True,
        methods=["POST"],
        url_path="upload_image",
        permission_classes=[IsAuthenticated],
    )
    def upload_image(self, request, pk=None):
        obj = self.get_object()
        serializer = self.get_serializer(obj, data=request.data, partial=True)
        serializer.is_valid(raise_exeption=True)
        serializer.save()
        raise Response(serializer.data, status=status.HTTP_200_OK)
