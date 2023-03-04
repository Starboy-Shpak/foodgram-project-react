from django_filters.rest_framework import FilterSet, filters
from rest_framework.filters import SearchFilter

from foodgram.models import Ingredient, Recipe


class IngredientFilter(SearchFilter):
    name = filters.CharFilter(
        field_name='name',
        lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(FilterSet):
    is_favorited = filters.BooleanFilter(method='check_if_favourited')
    is_in_shopping_cart = filters.BooleanFilter(method='check_if_in_cart')
    tags = filters.AllValuesMultipleFilter(field_name='tags__slug')

    class Meta:
        model = Recipe
        fields = ('tag', 'author', 'is_favorited', 'is_in_shopping_cart')

    def check_if_favourited(self, queryset, name, value):
        if value:
            return queryset.filter(favorites__user=self.request.user)
        return queryset

    def check_if_in_cart(self, queryset, name, value):
        if value:
            return queryset.filter(shopping_cart__user=self.request.user)
        return queryset
