from rest_framework import generics, status
from rest_framework.exceptions import APIException
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from .models import User
from .serializers import UserSerializer
from .tasks import send_mail_for_new_users_task


class UserListView(generics.ListCreateAPIView, generics.UpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request: Request, *args, **kwargs) -> Response:
        many = isinstance(request.data, list)
        serializer = self.get_serializer(data=request.data, many=many)
        serializer.is_valid(raise_exception=True)

        instances = self.perform_create(serializer)
        if not isinstance(instances, list):
            instances = [instances]
        emails = [instance.email for instance in instances]
        send_mail_for_new_users_task.delay(emails)

        if many:
            result_data = list(serializer.data)
        else:
            result_data = serializer.data

        return Response(result_data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer) -> User | list[User]:
        return serializer.save()

    def update(self, request: Request, *args, **kwargs) -> Response:
        many = isinstance(request.data, list)
        partial = kwargs.pop("partial", False)

        if isinstance(request.data, list):
            data = request.data
        elif isinstance(request.data, dict):
            data = [request.data]
        else:
            raise APIException("Неизвестный формат входных данных")

        ids = self.get_validate_ids(data)
        id_instances = self.get_id_instances(ids)

        serializers = []
        for row in data:
            instance = id_instances[row["id"]]
            serializer = self.get_serializer(instance, data=row, partial=partial)
            serializer.is_valid(raise_exception=True)
            serializers.append(serializer)

        for serializer in serializers:
            self.perform_update(serializer)

        if many:
            result_data = list(serializer.data for serializer in serializers)
        else:
            result_data = serializers[0].data

        return Response(result_data)

    def get_validate_ids(self, data: list[dict]) -> list[int]:
        ids = []
        for row in data:
            if "id" not in row:
                raise APIException("Не передан id")
            ids.append(row["id"])
        if len(ids) != len(set(ids)):
            raise APIException("Множественное обновление по одному id")
        return ids

    def get_id_instances(self, ids: list[int]) -> dict[int, User]:
        instances = self.filter_queryset(self.get_queryset()).filter(id__in=ids)
        return {instance.id: instance for instance in instances}


class CurrentUserView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self) -> User:
        return self.request.user  # type: ignore
