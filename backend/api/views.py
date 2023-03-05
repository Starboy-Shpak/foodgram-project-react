import django_filters.rest_framework
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import SAFE_METHODS, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from api.filters import IngredientsFilter, RecipesFilter
from api.pagination import CustomPagination
from api.permissions import AuthorPermission
from api.serializers import (CustomUserSerializer, FavouriteSerializer,
                             FollowSerializer, GetMyRecipeSerializer,
                             MyIngredientSerializer, MyTagSerializer,
                             PostMyRecipeSerializer, ShoppingCartSerializer)
from foodgram.models import (Favorite, Ingredient, Recipe, AmountIngredient,
                             ShoppingCart, Tag)
from users.models import Subscription, User


class FoodgramUsersViewSet(UserViewSet):
    '''Вьюсет для пользователей'''

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
        user = request.user
        queryset = User.objects.filter(following__user=user)
        pages = self.paginate_queryset(queryset)
        serializer = FollowSerializer(
            pages,
            many=True,
        )
        return self.get_paginated_response(serializer.data)

        # queryset = User.objects.filter(following__user=request.user)
        # page = self.paginate_queryset(queryset)
        # serializer = FollowSerializer(page,
        #                               many=True,
        #                               context={'request': request})
        # return self.get_paginated_response(serializer.data)


class RecipeViewSet(ModelViewSet):
    '''Вьюсет для рецептов'''

    queryset = Recipe.objects.all()
    serializer_class = None
    permission_classes = (AuthorPermission,)
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)
    filterset_class = RecipesFilter
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if self.request.method not in SAFE_METHODS:
            return PostMyRecipeSerializer
        return GetMyRecipeSerializer

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
        return self.post_action(Favorite, FavouriteSerializer, request, pk)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk):
        return self.delete_action(Favorite, request, pk)

    @action(
        detail=True,
        methods=['POST'],
        permission_classes=(IsAuthenticated,))
    def shopping_cart(self, request, pk):
        return self.post_action(
            ShoppingCart,
            ShoppingCartSerializer,
            request,
            pk)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk):
        return self.delete_action(
            ShoppingCart,
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
        ).order_by('ingredient__name').annotate(amount=Sum('amount'))

        return self.sending(queryset)

    def sending(self, queryset):
        text_to_print = 'Нужно купить:'
        for product in queryset:

            text_to_print += (
                '\n'
                + str(Ingredient.objects.get(
                    name=product['ingredient__name']).name)
                + ' '
                + str(product['amount'])
                + ' '
                + str(Ingredient.objects.get(
                    name=product['ingredient__name']).measurement_unit))

        response = HttpResponse(text_to_print, content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename=foodgram_products.txt')

        return response


class TagViewSet(ModelViewSet):
    '''Вьюсет для тегов'''

    queryset = Tag.objects.all()
    serializer_class = MyTagSerializer
    permission_classes = (AuthorPermission,)
    pagination_class = None


class IngredintViewSet(ModelViewSet):
    '''Вьюсет для ингредиентов'''

    queryset = Ingredient.objects.all()
    serializer_class = MyIngredientSerializer
    permission_classes = (AuthorPermission,)
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)
    pagination_class = None
    filterset_class = IngredientsFilter
