from django.contrib.auth.models import AbstractUser
from django.db import models


class UserFoodgram(AbstractUser):
    """Кастомная модель пользователя."""

    email = models.EmailField(
        'email',
        max_length=254, unique=True
    )
    password = models.CharField(
        'password',
        max_length=150)
    first_name = models.CharField(
        'first_name',
        max_length=150,
        blank=False, null=False)
    last_name = models.CharField(
        'last_name',
        max_length=150,
        blank=False, null=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name', 'password']

    class Meta:
        ordering = ['id']
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Subscription(models.Model):
    """Модель подписок."""
    user = models.ForeignKey(
        UserFoodgram,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        UserFoodgram,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор'
    )

    class Meta:
        verbose_name = 'подписка'
        verbose_name_plural = 'подписки'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'author'),
                name='unique_subscription'
            )
        ]

    def __str__(self):
        return f'Пользователь {self.user} подписался на {self.author}'

