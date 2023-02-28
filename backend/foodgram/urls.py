from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import IngredintViewSet, RecipeViewSet, TagViewSet

app_name = 'foodgram'

router = DefaultRouter()
router.register(r'ingredients', IngredintViewSet, basename='ingredients')
router.register(r'recipes', RecipeViewSet, basename='recipes')
router.register(r'tags', TagViewSet, basename='tags')

urlpatterns = [
    path('', include(router.urls)),
]
