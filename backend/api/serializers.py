from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import status, serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import SerializerMethodField
from drf_extra_fields.fields import Base64ImageField
from djoser.serializers import UserCreateSerializer, UserSerializer

from foodgram.models import (AmountIngredient, Ingredient, Recipe,
                             ShoppingList, Tag, Favorite)
from users.models import Subscription

User = get_user_model()


class CustomUserCreateSerializer(UserCreateSerializer):

    class Meta:
        model = User
        fields = (
            'email', 'username', 'first_name', 'last_name', 'password',
        )


class CustomUserSerializer(UserSerializer):

    is_subscribed = SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
        )

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Subscription.objects.filter(user=user, author=obj).exists()


class FollowSerializer(CustomUserSerializer):

    recipes_count = SerializerMethodField()
    recipes = SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes_count', 'recipes',
        )
        read_only_fields = ('email', 'username', 'first_name', 'last_name'),

    def validate(self, data):
        author_id = self.context.get(
            'request'
        ).parser_context.get('kwargs').get('id')
        author = get_object_or_404(User, id=author_id)
        user = self.context.get('request').user
        if user.author.filter(author=author_id).exists():
            raise ValidationError(
                detail='Подписка уже существует',
                code=status.HTTP_400_BAD_REQUEST,
            )
        if user == author:
            raise ValidationError(
                detail='Нельзя подписаться на самого себя',
                code=status.HTTP_400_BAD_REQUEST,
            )
        return data

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        recipes = obj.recipes.all()
        if limit:
            recipes = recipes[: int(limit)]
        serializer = FavoriteRecipesSerializer(
            recipes, many=True, read_only=True,
        )
        return serializer.data


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = '__all__'


class AmountIngredientSerializer(serializers.ModelSerializer):

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = AmountIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeReadSerializer(serializers.ModelSerializer):

    tags = TagSerializer(read_only=False, many=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = AmountIngredientSerializer(
        many=True, source='in_recipes'
    )
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image',
            'text', 'cooking_time',
        )

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return obj.favorites.filter(user=request.user).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return obj.shopping_cart.filter(user=request.user).exists()


class CreateRecipeSerializer(serializers.ModelSerializer):

    ingredients = AmountIngredientSerializer(many=True,)
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all(),
        error_messages={'does_not_exist': 'Такого тега не существует'}
    )
    image = Base64ImageField()
    author = UserSerializer(read_only=True)
    cooking_time = serializers.IntegerField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'name',
            'image', 'text', 'cooking_time',
        )

    def validate_tags(self, tags):
        for tag in tags:
            if not Tag.objects.filter(id=tag.id).exists():
                raise serializers.ValidationError(
                    'Такого тега не существует'
                )
        return tags

    def validate_cooking_time(self, cooking_time):
        if cooking_time < 1:
            raise serializers.ValidationError(
                'Время готовки должно быть не менее одной минуты'
            )
        return cooking_time

    def validate_ingredients(self, ingredients):
        ingredients_list = []
        if not ingredients:
            raise serializers.ValidationError('Отсутствуют ингредиенты')
        for ingredient in ingredients:
            if ingredient['id'] in ingredients_list:
                raise serializers.ValidationError(
                    'Ингредиенты должны быть уникальны'
                )
            ingredients_list.append(ingredient['id'])
            if int(ingredient.get('amount')) < 1:
                raise serializers.ValidationError(
                    'Количество ингредиента более 0'
                )
        return ingredients

    def create_ingredients(self, recipe, ingredients):
        ingredient_list = []
        for data in ingredients:
            ingredient_list.append(
                AmountIngredient(
                    ingredient=data.pop('id'),
                    amount=data.pop('amount'), recipe=recipe
                )
            )
        AmountIngredient.objects.bulk_create(ingredient_list)

    def create(self, data):
        tags = data.pop('tags')
        ingredients = data.pop('ingredients')
        recipe = Recipe.objects.create(author=self.context.get('request').user,
                                       **data)
        self.create_ingredients(recipe, ingredients)
        recipe.tags.set(tags)
        return recipe

    def update(self, instance, data):
        if 'tags' in data:
            instance.tags.set(
                data.pop('tags'))
        if 'ingredients' in data:
            ingredients = data.pop('ingredients')
            instance.ingredients.clear()
            self.create_ingredients(ingredients, instance)
        return super().update(instance, data)

    def to_representation(self, instance):
        return RecipeReadSerializer(instance, context={
            'request': self.context.get('request')
        }).data


class FavoriteRecipesSerializer(serializers.ModelSerializer):

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')

    def validate(self, data):
        user = data['user']
        if user.favorites.filter(recipe=data['recipe']).exists():
            raise serializers.ValidationError(
                'Рецепт уже был добавлен в избранное.'
            )
        return data


class ShoppingCartSerializer(serializers.ModelSerializer):

    class Meta:
        model = ShoppingList
        fields = ('user', 'recipe')

    def validate(self, data):
        user = data['user']
        if user.shopping_cart.filter(recipe=data['recipe']).exists():
            raise serializers.ValidationError(
                'Рецепт уже добавлен в корзину'
            )
        return data

    def to_representation(self, instance):
        return FavoriteRecipesSerializer(
            instance.recipe,
            context={'request': self.context.get('request')}
        ).data
