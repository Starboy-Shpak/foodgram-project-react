from datetime import datetime

from config.pagination import CustomPagination
from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (SAFE_METHODS, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST

from foodgram.models import (AmountIngredient, Favorite, Ingredient, Recipe,
                             ShoppingList, Tag)

from .filters import IngredientFilter, RecipeFilter
from .permissions import AuthorPermission
from .serializers import (CreateRecipeSerializer, FavoriteRecipesSerializer,
                          IngredientSerializer, RecipeReadSerializer,
                          ShoppingCartSerializer, TagSerializer)

User = get_user_model()

@extend_schema_view(
    get=extend_schema(summary='Ингредиенты рецепта', tags=['Ингредиенты']),
    list=extend_schema(summary='Список тэгов Search', tags=['Ингредиенты']),
)
class IngredintViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()
    permission_classes = (IsAuthenticatedOrReadOnly,)
    filter_backends = (IngredientFilter,)
    search_fields = ('^name',)
    pagination_class = None


@extend_schema_view(
    get=extend_schema(summary='Тэг рецепта', tags=['Тэги']),
    list=extend_schema(summary='Список тэгов Search', tags=['Тэги']),
)
class TagViewSet(viewsets.ModelViewSet):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = None


@extend_schema_view(
    perform_create=extend_schema(summary='Создать рецепт', tags=['Рецепты']),
    get=extend_schema(summary='Получить рецепт', tags=['Рецепты']),
    put=extend_schema(summary='Изменить рецепт', tags=['Рецепты']),
    patch=extend_schema(summary='Изменить частично рецепт', tags=['Рецепты']),
    delete=extend_schema(summary='Удалить рецепт', tags=['Рецепты']),
    list=extend_schema(summary='Список рецептов Search', tags=['Рецепты']),
)
class RecipeViewSet(viewsets.ModelViewSet):
    serializer_class = CreateRecipeSerializer
    queryset = Recipe.objects.all()
    permission_classes = (AuthorPermission,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    pagination_class = CustomPagination

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeReadSerializer
        return CreateRecipeSerializer

    @action(
        detail=True, methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk):
        user = request.user

        if request.method == 'POST':
            return self.add_to(Favorite, user, pk)

        if request.method == 'DELETE':
            return self.delete_from(Favorite, user, pk)

    @action(
        detail=True, methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk):
        user = request.user

        if request.method == 'POST':
            return self.add_to(ShoppingList, user, pk)

        if request.method == 'DELETE':
            return self.delete_from(ShoppingList, user, pk)

    def add_to(self, model, user, pk):
        if model.objects.filter(user=user, recipe__id=pk).exists():
            return Response(
                {'errors': 'Рецепт уже был добавлен!'},
                status=status.HTTP_400_BAD_REQUEST
            )
        recipe = get_object_or_404(Recipe, id=pk)
        model.objects.create(user=user, recipe=recipe)
        serializer = FavoriteRecipesSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_from(self, model, user, pk):
        obj = model.objects.filter(user=user, recipe__id=pk)
        if obj.exists():
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'errors': 'Рецепт уже был удален!'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=False, permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        user = request.user
        if not user.shopping_cart.exists():
            return Response(status=HTTP_400_BAD_REQUEST)
        ingredients = AmountIngredient.objects.filter(
            recipe__shopping_cart__user=user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(amount=Sum('amount'))
        today = datetime.today()
        shopping_list = (
            f'Список покупок пользователя: {user}\n'
            f'Дата: {today:%Y-%m-%d}\n'
        )
        shopping_list += '\n'.join([
            f'- {ingredient["ingredient__name"]} - {ingredient["amount"]} '
            f'{ingredient["ingredient__measurement_unit"]}'
            for ingredient in ingredients
        ])
        filename = f'{user}_shopping_list.txt'
        response = HttpResponse(shopping_list, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response
