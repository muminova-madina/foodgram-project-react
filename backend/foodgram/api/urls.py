from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import (IngredientViewSet, RecipeViewSet,
                       SubscriptionsNumberViewSet, SubscriptionViewSet,
                       TagViewSet, UsersViewSet)

router = DefaultRouter()
router.register('recipes', RecipeViewSet, basename='recipes')
router.register('tags', TagViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('users', UsersViewSet, basename='users')
router.register('users/subscriptions', SubscriptionsNumberViewSet,
                basename='subscriptions_list')
router.register(r'users/(?P<id>\d+)/subscribe', SubscriptionViewSet,
                basename='subscribe')

urlpatterns = [
    path('', include(router.urls)),
    path(r'auth/', include('djoser.urls.authtoken')),
    path('', include('djoser.urls')),
]
