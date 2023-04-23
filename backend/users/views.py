from django.contrib.auth import get_user_model
from djoser.views import UserViewSet
from rest_framework import exceptions
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated

from api.pagination import CustomPagination
from api.utils import create_or_delete_record
from users.serializers import SubscriptionSerializer

User = get_user_model()


class CustomUserViewSet(UserViewSet):
    permission_classes = (IsAuthenticated,)
    pagination_class = CustomPagination

    @action(
        detail=False,
        methods=('get',),
        serializer_class=SubscriptionSerializer,
        permission_classes=(IsAuthenticated,),
    )
    def subscriptions(self, request):
        authors = self.request.user.follower.values('author__id')
        queryset = User.objects.filter(pk__in=authors)
        serializer = self.get_serializer(
            self.paginate_queryset(queryset), many=True
        )

        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=('post', 'delete'),
        serializer_class=SubscriptionSerializer,
    )
    def subscribe(self, request, id=None):
        user = self.request.user
        author = get_object_or_404(User, pk=id)
        in_follow = user.follower.filter(author=author)
        if request.method == 'POST' and user == author:
            raise exceptions.ValidationError('you can`t subscribe to yourself')

        return create_or_delete_record(
            request=request,
            record=in_follow,
            serializer_data=self.get_serializer(author).data,
            params={'author': author},
        )
