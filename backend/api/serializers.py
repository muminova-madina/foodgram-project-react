from django.contrib.auth import get_user_model
from django.db import transaction
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            RecipeTag, ShoppingCart, Tag)
from users.serializers import CustomUserSerializer

User = get_user_model()


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Ингредиенты."""

    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'measurement_unit']


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Тег."""

    class Meta:
        model = Tag
        fields = ['id', 'name', 'color', 'slug']
        read_only_fields = ['name', 'color']


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Рецепты."""
    image = Base64ImageField()
    author = CustomUserSerializer(read_only=True)
    ingredients = IngredientSerializer(many=True)
    tags = TagSerializer(many=True)
    is_favorited = serializers.SerializerMethodField(
        method_name='get_is_favorited', read_only=True)
    is_in_shoppingcart = serializers.SerializerMethodField(
        method_name='get_is_in_shoppingcart', read_only=True)

    class Meta:
        model = Recipe
        fields = ('id', 'author', 'name', 'text', 'ingredients',
                  'tags', 'cooking_time', 'is_favorited',
                  'is_in_shoppingcart', 'image')
        read_only_fields = ('is_favorited', 'is_in_shopping_cart')

    def get_ingredients(self, obj):
        ingredients = RecipeIngredient.objects.filter(recipe=obj)
        return RecipeIngredientSerializer(ingredients, many=True).data

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Favorite.objects.filter(
            user=request.user, recipe_id=obj).exists()

    def get_is_in_shoppingcart(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(
            user=request.user, recipe_id=obj).exists()


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор модели, связывающей ингредиенты и рецепт."""
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ['__all__']


class AddIngredientRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор добавления ингредиента в рецепт."""
    id = serializers.IntegerField()
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ['id', 'amount']


class CreateRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор создания или обновления рецепта."""
    author = CustomUserSerializer(read_only=True)
    ingredients = AddIngredientRecipeSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = [
            'id',
            'author',
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time'
        ]
        read_only_fields = ['author']

    def validate(self, data):
        ingredients = self.initial_data.get('ingredients')
        ingredients_data = set()
        for element in ingredients:
            amount = element['amount']
            if int(amount) < 1:
                raise serializers.ValidationError({
                    'amount': 'Количество ингредиента должно быть больше 0!'
                })
            if element['id'] in ingredients_data:
                raise serializers.ValidationError({
                    'ingredient': 'Ингредиенты должны быть уникальными!'
                })
            ingredients_data.add(element['id'])
        return data

    @staticmethod
    def create_recipe_ingredients(ingredients, recipe):
        RecipeIngredient.objects.bulk_create(
            [
                RecipeIngredient(
                    recipe_id=recipe.id,
                    ingredient_id=ingredient['id'],
                    amount=ingredient['amount'],
                )
                for ingredient in ingredients
            ]
        )

    def tag(self, tags, recipe):
        recipe_tags = [RecipeTag(recipe=recipe, tag=tag) for tag in tags]
        RecipeTag.objects.bulk_create(recipe_tags)

    @transaction.atomic
    def create(self, validated_data):
        """Создание рецепта только авторизованному пользователю."""
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)

        self.create_recipe_ingredients(ingredients, recipe)
        recipe.tags.set(tags)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        """Изменение рецепта автором рецепта."""
        tags = validated_data.pop('tags', None)
        if tags is not None:
            instance.tags.set(tags)

        ingredients = validated_data.pop('ingredients', None)
        if ingredients is not None:
            instance.ingredients.clear()
        self.create_recipe_ingredients(ingredients, instance)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return RecipeSerializer(instance, context={
            'request': self.context.get('request')
        }).data


class FavoritListSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения избранного."""

    class Meta:
        model = Recipe
        fields = ['id', 'name', 'image', 'cooking_time']
