from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import UniqueConstraint

User = get_user_model()


class Ingredient(models.Model):
    """Модель ингредиента."""
    name = models.CharField(
        max_length=100,
        verbose_name='Название ингредиента')
    measurement_unit = models.CharField(
        max_length=200,
        verbose_name='Единица измерения')

    class Meta:
        ordering = ['name']
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique ingredient')
        ]

    def __str__(self):
        return self.name


class Tag(models.Model):
    """Модель тэга."""
    name = models.CharField(
        max_length=100, unique=True,
        verbose_name='Название тега')
    color = models.CharField(
        max_length=7, unique=True,
        verbose_name='Цвет')
    slug = models.SlugField(
        max_length=100,
        unique=True,
        verbose_name='Слаг')

    class Meta:
        ordering = ['name']
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Модель рецепта."""
    author = models.ForeignKey(
        User,
        related_name='recipes',
        on_delete=models.CASCADE,
        verbose_name='Автор рецепта')
    name = models.CharField(
        max_length=100,
        verbose_name='Название рецепта')
    image = models.ImageField(
        upload_to='recipes/images',
        verbose_name='Изображение')
    text = models.TextField(
        verbose_name='Описание рецепта',
        help_text='Введите описание рецепта')
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Ингредиенты')
    tags = models.ManyToManyField(
        Tag, through='RecipeTag',
        verbose_name='Тэги', related_name='tags')
    cooking_time = models.PositiveIntegerField(
        verbose_name='Время приготовления',
        validators=[
            MinValueValidator(1,
                              message='Время приготовление должно быть не менее 1 минуты!'
                              ),
            MaxValueValidator(1440,
                              message='Время приготовление не может превышать 1440 минут!'
                              )
        ])
    pub_date = models.DateTimeField(verbose_name='Время публикации',
                                    auto_now_add=True)

    class Meta:
        ordering = ['pub_date']
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """Модель связи рецепта и ингредиента."""
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE,
        verbose_name='Рецепт')
    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.CASCADE,
        verbose_name='Ингредиент')
    amount = models.IntegerField(
        verbose_name='Количество',
        validators=[MinValueValidator(1),
                    MaxValueValidator(10000)])

    class Meta:
        constraints = [UniqueConstraint(
            fields=['recipe', 'ingredient'],
            name='recipe_ingredient_unique'
        )]

    def __str__(self):
        return f'{self.amount} {self.ingredient.measurement_unit} {self.ingredient.name}'


class RecipeTag(models.Model):
    """ Модель связи тега и рецепта. """

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        verbose_name='Тег'
    )

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['recipe', 'tag'],
                name='recipe_tag_unique'
            )
        ]

    def __str__(self):
        return f'{self.tag.name} {self.ingredient.name}'


class ShoppingCart(models.Model):
    """ Модель корзины. """

    user = models.ForeignKey(
        User,
        related_name='shopping_list',
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name='in_shopping_list',
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['user', 'recipe'],
                name='user_shoppingcart_unique'
            )
        ]

    def __str__(self):
        return f'{self.recipe_id} {self.user_id}'


class Favorite(models.Model):
    """ Модель избранного. """

    user = models.ForeignKey(
        User,
        related_name='favorites',
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='in_favorite',
        verbose_name='Рецепт'
    )

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['user', 'recipe'],
                name='user_favorite_unique'
            )
        ]

    def __str__(self):
        return f'{self.recipe_id} {self.user_id}'
