from django.contrib.auth import get_user_model
from django.utils.datastructures import MultiValueDictKeyError
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import LowercaseEmailField
from rest_framework import serializers

from api.utils import get_recipe_serializer

User = get_user_model()


class CustomUserCreateSerializer(UserCreateSerializer):
    email = LowercaseEmailField()

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'password',
        )


class CustomUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return obj.following.filter(user_id=user.id).exists()

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'is_subscribed',
        )


class SubscriptionSerializer(CustomUserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    def get_recipes(self, obj):
        author_recipes = obj.recipes.all()
        try:
            recipes_limit = self.context.get('request').GET['recipes_limit']
            author_recipes = author_recipes[: int(recipes_limit)]
        except (MultiValueDictKeyError, ValueError):
            pass

        if author_recipes:
            serializer = get_recipe_serializer()(
                author_recipes,
                many=True,
            )
            return serializer.data

        return []

    @staticmethod
    def get_recipes_count(obj):
        return obj.recipes.count()

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'is_subscribed',
            'recipes',
            'recipes_count',
        )
