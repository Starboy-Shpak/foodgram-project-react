from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum
from django.http import HttpResponse
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (SAFE_METHODS, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
# from rest_framework.status import HTTP_400_BAD_REQUEST
from djoser.views import UserViewSet

from api.pagination import CustomPagination
from foodgram.models import (AmountIngredient, Favorite, Ingredient, Recipe,
                             ShoppingList, Tag)
from users.models import Subscription
from api.filters import IngredientFilter, RecipeFilter
from api.permissions import AuthorPermission
from api.serializers import (FollowSerializer, CustomUserSerializer,
                             CreateRecipeSerializer, FavoriteRecipesSerializer,
                             IngredientSerializer, RecipeReadSerializer,
                             TagSerializer, ShoppingCartSerializer)

User = get_user_model()


class FoodgramUsersViewSet(UserViewSet):

    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    pagination_class = CustomPagination

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=(IsAuthenticated,),
        url_path='subscribe',
        url_name='subscribe',)
    def follow(self, request, id):
        '''Подписка/отписка'''
        author = get_object_or_404(User, id=id)
        if request.method == 'POST':
            serializer = FollowSerializer(author,
                                          data=request.data,
                                          context={"request": request})
            serializer.is_valid(raise_exception=True)
            Subscription.objects.create(user=request.user, author=author)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            get_object_or_404(
                Subscription,
                user=request.user,
                author=author).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.data, status=status.HTTP_404_NOT_FOUND)

    @action(
        detail=False,
        methods=['GET'],
        permission_classes=(IsAuthenticated,),
        url_path='subscriptions',
        url_name='subscriptions',)
    def follows(self, request):
        '''Список подписок'''
        queryset = User.objects.filter(author__user=request.user)
        page = self.paginate_queryset(queryset)
        serializer = FollowSerializer(page,
                                      many=True,
                                      context={'request': request})
        return self.get_paginated_response(serializer.data)


class IngredintViewSet(viewsets.ReadOnlyModelViewSet):

    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()
    permission_classes = (IsAuthenticatedOrReadOnly,)
    filter_backends = (IngredientFilter,)
    search_fields = ('^name',)
    pagination_class = None


class TagViewSet(viewsets.ModelViewSet):

    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):

    serializer_class = None
    queryset = Recipe.objects.all()
    permission_classes = (AuthorPermission,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if self.request.method not in SAFE_METHODS:
            return CreateRecipeSerializer
        return RecipeReadSerializer

    @staticmethod
    def post_action(model=None, serializer=None, request=None, pk=None):
        serializer = serializer(
            data={'user': request.user.id, 'recipe': pk},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status.HTTP_201_CREATED)

    @staticmethod
    def delete_action(model=None, request=None, pk=None):
        get_object_or_404(
            model,
            recipe__id=pk,
            user=get_object_or_404(User, id=request.user.id)).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['POST'],
        permission_classes=(IsAuthenticated,))
    def favorite(self, request, pk):
        return self.post_action(
            Favorite, FavoriteRecipesSerializer, request, pk,
        )

    @favorite.mapping.delete
    def delete_favorite(self, request, pk):
        return self.delete_action(Favorite, request, pk)

    @action(
        detail=True,
        methods=['POST'],
        permission_classes=(IsAuthenticated,))
    def shopping_cart(self, request, pk):
        return self.post_action(
            ShoppingList,
            ShoppingCartSerializer,
            request,
            pk)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk):
        return self.delete_action(
            ShoppingList,
            request,
            pk)

    @action(
        detail=False,
        methods=['GET'],
        permission_classes=(IsAuthenticated,),)
    def download_shopping_cart(self, request):
        queryset = AmountIngredient.objects.filter(
            recipe__shopping_cart__user=request.user
        ).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).order_by('ingredient__name').annotate(quantity=Sum('amount'))

        return self.sending(queryset)

    def sending(self, queryset):
        today = timezone.now().day
        shopping_list = (
            f'Список покупок:\n'
            f'Дата: {today:%Y-%m-%d}\n'
        )
        shopping_list += '\n'.join([
            f'- {ingredient["ingredient__name"]} - {ingredient["quantity"]} '
            f'{ingredient["ingredient__measurement_unit"]}'
            for ingredient in queryset
        ])
        filename = 'shopping_list.txt'
        response = HttpResponse(shopping_list, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename={filename}'

        return response

    # def perform_create(self, serializer):
    #     serializer.save(author=self.request.user)

    # def get_serializer_class(self):
    #     if self.request.method in SAFE_METHODS:
    #         return RecipeReadSerializer
    #     return CreateRecipeSerializer

    # @action(
    #     detail=True, methods=['post', 'delete'],
    #     permission_classes=[IsAuthenticated]
    # )
    # def favorite(self, request, pk):
    #     user = request.user

    #     if request.method == 'POST':
    #         return self.add_to(Favorite, user, pk)

    #     if request.method == 'DELETE':
    #         return self.delete_from(Favorite, user, pk)

    # @action(
    #     detail=True, methods=['post', 'delete'],
    #     permission_classes=[IsAuthenticated]
    # )
    # def shopping_cart(self, request, pk):
    #     user = request.user

    #     if request.method == 'POST':
    #         return self.add_to(ShoppingList, user, pk)

    #     if request.method == 'DELETE':
    #         return self.delete_from(ShoppingList, user, pk)

    # def add_to(self, model, user, pk):
    #     if model.objects.filter(user=user, recipe__id=pk).exists():
    #         return Response(
    #             {'errors': 'Рецепт уже был добавлен!'},
    #             status=status.HTTP_400_BAD_REQUEST
    #         )
    #     recipe = get_object_or_404(Recipe, id=pk)
    #     model.objects.create(user=user, recipe=recipe)
    #     serializer = FavoriteRecipesSerializer(recipe)
    #     return Response(serializer.data, status=status.HTTP_201_CREATED)

    # def delete_from(self, model, user, pk):
    #     obj = model.objects.filter(user=user, recipe__id=pk)
    #     if obj.exists():
    #         obj.delete()
    #         return Response(status=status.HTTP_204_NO_CONTENT)
    #     return Response(
    #         {'errors': 'Рецепт уже был удален!'},
    #         status=status.HTTP_400_BAD_REQUEST
    #     )

    # @action(detail=False, permission_classes=[IsAuthenticated])
    # def download_shopping_cart(self, request):
        # user = request.user
        # if not user.shopping_cart.exists():
        #     return Response(status=HTTP_400_BAD_REQUEST)
        # ingredients = AmountIngredient.objects.filter(
        #     recipe__shopping_cart__user=user
        # ).values(
        #     'ingredient__name',
        #     'ingredient__measurement_unit'
        # ).annotate(quantity=Sum('amount'))
        # today = timezone.now().day
        # shopping_list = (
        #     f'Список покупок пользователя: {user}\n'
        #     f'Дата: {today:%Y-%m-%d}\n'
        # )
        # shopping_list += '\n'.join([
        #     f'- {ingredient["ingredient__name"]} - {ingredient["quantity"]} '
        #     f'{ingredient["ingredient__measurement_unit"]}'
        #     for ingredient in ingredients
        # ])
        # filename = f'{user}_shopping_list.txt'
        # response = HttpResponse(shopping_list, content_type='text/plain')
        # response['Content-Disposition'] = f'attachment; filename={filename}'
        # return response
