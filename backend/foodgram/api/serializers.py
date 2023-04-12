from django.contrib.auth import get_user_model
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            RecipeTag, ShoppingCart, Tag)
from users.models import Subscription, UserFoodgram

User = get_user_model()


class CustomUserCreateSerializer(UserCreateSerializer):
    """Сериализатор создания пользователя."""

    class Meta:
        model = User
        fields = [
            'email',
            'username',
            'first_name',
            'last_name',
            'password'
        ]


class CustomUserSerializer(UserSerializer):
    """Сериализатор модели пользователя."""
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = UserFoodgram
        fields = [
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'password'
        ]

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Subscription.objects.filter(
            user=request.user, author=obj
        ).exists()


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
        fields = ('id', 'author', 'name', 'text', 'ingredients', 'tags',
                  'cooking_time', 'is_favorited', 'is_in_shoppingcart', 'image')
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
            if int(amount) < 1 or int(amount) > 32:
                raise serializers.ValidationError({
                    'amount': 'Количество ингредиента должно быть больше 0!'
                })
            if element['id'] in ingredients_data:
                raise serializers.ValidationError({
                    'ingredient': 'Ингредиенты должны быть уникальными!'
                })
            ingredients_data.add(element['id'])
        return data

    def create_ingredients(self, ingredients, recipe):
        recipe_ingredients = []
        for element in ingredients:
            ingredient = Ingredient.objects.get(id=element['id'])
            recipe_ingredient = RecipeIngredient(
                ingredient=ingredient,
                recipe=recipe,
                amount=element['amount']
            )
            recipe_ingredients.append(recipe_ingredient)
        RecipeIngredient.objects.bulk_create(recipe_ingredients)

    def tag(self, tags, recipe):
        recipe_tags = [RecipeTag(recipe=recipe, tag=tag) for tag in tags]
        RecipeTag.objects.bulk_create(recipe_tags)

    def create(self, validated_data):
        """Создание рецепта только авторизованному пользователю."""
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)

        self.create_ingredients(ingredients, recipe)
        self.create_tags(tags, recipe)
        return recipe

    def update(self, instance, validated_data):
        """Изменение рецепта автором рецепта."""
        RecipeTag.objects.filter(recipe=instance).delete()
        RecipeIngredient.objects.filter(recipe=instance).delete()
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        self.create_ingredients(ingredients, instance)
        self.create_tags(tags, instance)
        instance.name = validated_data.pop('name')
        instance.text = validated_data.pop('text')
        if validated_data.get('image'):
            instance.image = validated_data.pop('image')
        instance.cooking_time = validated_data.pop('cooking_time')
        instance.save()
        return instance

    def to_representation(self, instance):
        return RecipeSerializer(instance, context={
            'request': self.context.get('request')
        }).data


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Списка Покупок."""
    recipe = RecipeSerializer()

    class Meta:
        model = ShoppingCart
        fields = ['user', 'recipe']

    def to_representation(self, instance):
        return ShoppingCartSerializer(instance.recipe, context={
            'request': self.context.get('request')
        }).data


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Избранное."""
    recipe = RecipeSerializer()

    class Meta:
        model = Favorite
        fields = ['user', 'recipe']


class FavoritListSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения избранного."""
    recipe = RecipeSerializer()

    class Meta:
        model = Recipe
        fields = ['id', 'name', 'image', 'cooking_time']


class SubscriptionsNumberSerializer(serializers.ModelSerializer):
    """Сериализатор отображения подписчиков пользователя."""
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count'
        ]

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Subscription.objects.filter(
            user=request.user, author=obj).exists()

    def get_recipes(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        recipes = Recipe.objects.filter(author=obj)
        limit = request.query_params.get('recipes_limit')
        if limit:
            recipes = recipes[:int(limit)]
        return FavoritListSerializer(
            recipes, many=True, context={'request': request}).data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj).count()


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор для модели подписок."""

    class Meta:
        model = Subscription
        fields = ['author', 'user']
        validators = [
            UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=['author', 'user'],
            )
        ]

    def to_representation(self, instance):
        return SubscriptionsNumberSerializer(instance.author, context={
            'request': self.context.get('request')
        }).data
