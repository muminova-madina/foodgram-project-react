from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from api.filters import RecipeFilter
from api.pagination import CustomPagination
from api.report import create_pdf_from_queryset
from api.serializers import (CreateRecipeSerializer, IngredientSerializer, RecipeSerializer,
                             TagSerializer, FavoritListSerializer)
from api.utils import create_or_delete_record
from recipes.models import (Ingredient, Recipe, Tag, RecipeIngredient)

User = get_user_model()


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для Рецептов."""
    queryset = Recipe.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = CustomPagination

    def get_serializer_class(self):
        """POST, PATCH или PUT-запрос"""
        if self.action in ['create', 'partial_update']:
            return CreateRecipeSerializer
        if self.action == 'update':
            return CreateRecipeSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=('post', 'delete'))
    def favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        in_favorite = recipe.in_favorite.filter(user=self.request.user)
        return create_or_delete_record(
            request=request,
            record=in_favorite,
            serializer_data=FavoritListSerializer(recipe).data,
            params={'recipe': recipe},
        )

    @action(detail=True, methods=('post', 'delete'))
    def shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        in_shopping_list = recipe.in_shopping_list.filter(
            user=self.request.user
        )
        return create_or_delete_record(
            request=request,
            record=in_shopping_list,
            serializer_data=FavoritListSerializer(recipe).data,
            params={'recipe': recipe},
        )

    @action(
        detail=False, methods=('get',), permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        user = self.request.user
        recipes = user.shopping_list.values('recipe__id')

        buy_list = (
            RecipeIngredient.objects.filter(recipe__in=recipes)
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(amount=Sum('amount'))
            .order_by('ingredient__name')
        )

        pdf_file = create_pdf_from_queryset(buy_list, user.username)
        return FileResponse(
            pdf_file, as_attachment=True, filename='buy_list.pdf'
        )


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
    search_fields = ['^name']
