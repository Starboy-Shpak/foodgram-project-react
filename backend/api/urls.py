from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (FoodgramUsersViewSet, IngredintViewSet,
                    RecipeViewSet, TagViewSet)

app_name = 'api'


router = DefaultRouter()
router.register(r'users', FoodgramUsersViewSet, basename='users')
router.register(r'ingredients', IngredintViewSet, basename='ingredients')
router.register(r'recipes', RecipeViewSet, basename='recipes')
router.register(r'tags', TagViewSet, basename='tags')

urlpatterns = [
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken'))
]

app_name = 'api'






# from foodgram.urls import urlpatterns as foodgram
# from users.urls import urlpatterns as users

# app_name = 'api'

# urlpatterns = []

# urlpatterns += users
# urlpatterns += foodgram
