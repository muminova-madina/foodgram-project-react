import csv

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from djoser.views import UserViewSet
from rest_framework import mixins, viewsets, permissions, filters
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend

from api.pagination import CustomPagination
from api.serializers import (IngredientSerializer, CreateRecipeSerializer,
                             RecipeSerializer, ShoppingCartSerializer,
                             TagSerializer, FavoriteSerializer,
                             SubscriptionSerializer, SubscriptionsNumberSerializer)
from recipes.models import Ingredient, Recipe, ShoppingCart, Favorite, Tag, User

from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

from users.models import Subscription


User = get_user_model()


class UsersViewSet(UserViewSet):
    """Получение списка пользователей и редактирование."""
    permission_classes = (IsAuthenticated,)
    pagination_class = CustomPagination


class SubscriptionViewSet(mixins.CreateModelMixin,
                          mixins.DestroyModelMixin,
                          viewsets.GenericViewSet):
    """Подписки и отписки."""
    permission_classes = [IsAuthenticated]
    serializer_class = SubscriptionSerializer

    @action(detail=True, methods=['post'])
    def subscribe(self, request, pk):
        author = get_object_or_404(User, pk=pk)
        serializer = self.get_serializer(data={'author': author.pk})
        serializer.is_valid(raise_exception=True)
        subscription = serializer.save(user=request.user)
        return Response(
            self.get_serializer(subscription).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['delete'])
    def unsubscribe(self, request, pk):
        author = get_object_or_404(User, pk=pk)
        subscription = get_object_or_404(
            Subscription, user=request.user, author=author
        )
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SubscriptionsNumberViewSet(mixins.ListModelMixin,
                                 viewsets.GenericViewSet):
    """Отображение подписок."""
    permission_classes = [IsAuthenticated]
    serializer_class = SubscriptionsNumberSerializer
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user
        return User.objects.filter(author__user=user)


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для Рецептов."""
    queryset = Recipe.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    #filterset_fields = ['author', 'tags__slug', 'is_favorited', 'is_in_shopping_cart']
    search_fields = ['name', 'ingredients__name', 'author__username']
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        """POST, PATCH или PUT-запрос"""
        if self.action in ['create', 'partial_update']:
            return CreateRecipeSerializer
        elif self.action == 'update':
            return CreateRecipeSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['get'])
    def shopping_list(self, request):
        recipe = self.get_object()
        user = request.user
        purchase = get_object_or_404(ShoppingCart, user=user, recipe=recipe)
        purchase.delete()
        return Response(status=204)

    @shopping_list.mapping.post
    def add_to_list(self, request):
        recipe = self.get_object()
        serializer = ShoppingCartSerializer(data={'recipe': recipe.id})
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.data, status=201)

    @action(detail=True, methods=['post'])
    def favorite(self, request):
        recipe = self.get_object()
        serializer = RecipeSerializer(recipe, data={'is_favorited': True}, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        Favorite.objects.get_or_create(user=request.user, recipe=recipe)
        return Response(serializer.data, status=200)

    @action(detail=True, methods=['delete'])
    def unfavorite(self, request):
        recipe = self.get_object()
        serializer = RecipeSerializer(recipe, data={'is_favorited': False}, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        Favorite.objects.filter(user=request.user, recipe=recipe).delete()
        return Response(status=204)


class TagViewSet(viewsets.ModelViewSet):
    """Вьюсет для Тега."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class IngredientViewSet(viewsets.ModelViewSet):
    """Вьюсет для Ингредиентов."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']


def get_content(queryset):
    content = []
    for item in queryset:
        recipe = item.recipe
        ingredients = recipe.ingredients.all()
        ingredients_list = [
            f'{ingredient.name} - {item.amount} {ingredient.unit}'
            for ingredient, item in zip(ingredients, item.items)
        ]
        recipe_info = {
            'id': recipe.id,
            'tags': [tag.slug for tag in recipe.tags.all()],
            'author': recipe.author.username,
            'ingredients': ingredients_list,
            'is_favorited': recipe.is_favorited,
            'is_in_shopping_cart': recipe.is_in_shopping_cart,
            'name': recipe.name,
            'image': recipe.image.url,
            'text': recipe.text,
            'cooking_time': recipe.cooking_time,
        }
        content.append(recipe_info)
    return content


class ShoppingCartViewSet(viewsets.ModelViewSet):
    """Вьюсет для Списка Покупок."""
    queryset = ShoppingCart.objects.all()
    serializer_class = ShoppingCartSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(user=self.request.user)


@csrf_exempt
def download_shopping_cart(request):
    shopping_cart_items = ShoppingCart.objects.filter(user=request.user)
    response = HttpResponse(content_type='text/plain')
    response['Content-Disposition'] = 'attachment; filename="shopping_cart.txt"'

    writer = csv.writer(response, delimiter='\t')
    for item in shopping_cart_items:
        writer.writerow([item.ingredient.name, item.amount])

    return response


class FavoriteViewSet(viewsets.ModelViewSet):
    """Вьюсет для Избранного."""
    queryset = Favorite.objects.all()
    serializer_class = FavoriteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(user=self.request.user)

    def create(self, request):
        recipe_id = request.data.get('recipe')
        if not recipe_id:
            return Response({'recipe': 'Это поле обязательно для заполнения!'},
                            status=status.HTTP_400_BAD_REQUEST)

        recipe = Recipe.objects.filter(id=recipe_id).first()
        if not recipe:
            return Response({'recipe': 'Неверное значени!'},
                            status=status.HTTP_400_BAD_REQUEST)

        favorite, created = Favorite.objects.get_or_create(user=request.user,
                                                           recipe=recipe)
        if not created:
            return Response({'error': 'Рецепт уже в избранном!'},
                            status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(favorite)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, pk=None):
        favorite = Favorite.objects.filter(user=request.user, id=pk).first()
        if not favorite:
            return Response({'error': 'Favorite recipe not found.'},
                            status=status.HTTP_404_NOT_FOUND)

        favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
