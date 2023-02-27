from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import IngredintViewSet, RecipeViewSet, TagViewSet

app_name = 'foodgram'

router = DefaultRouter()
router.register(r'ingredients', IngredintViewSet, basename='ingredients')
router.register(r'tags', RecipeViewSet, basename='tags')
router.register(r'recipes', TagViewSet, basename='recipes')

urlpatterns = [
    path('', include(router.urls)),
]
