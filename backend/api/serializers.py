from django.core.validators import MinValueValidator, ValidationError
from django.db import IntegrityError
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework.fields import SerializerMethodField
from rest_framework.serializers import (IntegerField, ModelSerializer,
                                        PrimaryKeyRelatedField, ReadOnlyField)

from foodgram.models import (Favourite, Ingredient, Recipe, RecipeIngredients,
                             ShoppingCart, Tag)
from users.models import User


class CustomUserCreateSerializer(UserCreateSerializer):
    '''Сериалайзер создания пользователя'''

    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name', 'password',)


class CustomUserSerializer(UserSerializer):
    '''Сериалайзер пользователя'''

    is_subscribed = SerializerMethodField('check_subscribiton')

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username',
            'first_name', 'last_name',
            'is_subscribed',)

    def check_subscribiton(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return request.user.follower.filter(author=obj).exists()


class FollowSerializer(CustomUserSerializer):
    '''Сериалайзер функции подписки'''

    recipes = SerializerMethodField('check_his_recipes')
    recipes_count = SerializerMethodField('count_his_recipes')

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username',
            'first_name', 'last_name',
            'is_subscribed', 'recipes',
            'recipes_count',
        )
        read_only_fields = ('email', 'username', 'first_name', 'last_name')

    def check_his_recipes(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        recipes_limit = request.GET.get('recipes_limit')
        recipes = obj.recipes.all()
        if recipes_limit:
            recipes = (obj.recipes.all())[:int(recipes_limit)]
        return GetMyRecipeSerializer(recipes, many=True).data

    @staticmethod
    def count_his_recipes(obj):
        return obj.recipes.count()


class MyTagSerializer(ModelSerializer):
    '''Сериалайзер тегов'''

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug',)


class MyIngredientSerializer(ModelSerializer):
    '''Сериалайзер ингредиентов'''

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit',)


class RecipeIngredientsSerializer(ModelSerializer):
    '''Сериалайзер отображения рецептов'''

    id = ReadOnlyField(
        source='ingredient.id')
    name = ReadOnlyField(
        source='ingredient.name')
    measurement_unit = ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredients
        fields = ('id', 'name', 'measurement_unit', 'amount',)


class GetMyRecipeSerializer(ModelSerializer):
    '''Сериалайзер чтения рецептов'''

    tags = MyTagSerializer(many=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = SerializerMethodField('get_ingredients_for_recipe')
    is_favorited = SerializerMethodField('check_if_favourited')
    is_in_shopping_cart = SerializerMethodField('check_if_in_cart')
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'tag', 'author', 'ingredients',
                  'is_favorited', 'is_in_shopping_cart',
                  'title', 'image', 'discription', 'cooking_time',)

    def get_ingredients_for_recipe(self, obj):
        ingredients = RecipeIngredients.objects.filter(recipe=obj)

        return RecipeIngredientsSerializer(ingredients, many=True).data

    def check_if_favourited(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return request.user.favorites.filter(recipe=obj).exists()

    def check_if_in_cart(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return request.user.shopping_cart.filter(recipe=obj).exists()


class AddIngredientsToRecipe(ModelSerializer):
    '''Сериалайзер добавления ингредиентов к рецепту'''

    id = IntegerField()
    amount = IntegerField()

    class Meta:
        model = RecipeIngredients
        fields = ('id', 'amount')


class PostMyRecipeSerializer(ModelSerializer):
    '''Сериалайзер создания/обновления рецептов'''

    ingredients = AddIngredientsToRecipe(many=True)
    tags = PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True)
    image = Base64ImageField()
    cooking_time = IntegerField(validators=(
        MinValueValidator(
            1,
            message='Укажите корректное время приготовления'),))

    class Meta:
        model = Recipe
        fields = ('ingredients', 'tag',
                  'image', 'title',
                  'discription', 'cooking_time',
                  )

    def validate_ingredients(self, data):
        if data:
            ingredient_ids = []
            for ingredient in data:
                if ingredient['id'] in ingredient_ids:
                    raise ValidationError({
                        'ingredients_uniqueness': 'Ингредиенты не уникальны'})
                ingredient_ids.append(ingredient['id'])
                if int(ingredient['amount']) <= 0:
                    raise ValidationError({
                        'ingredients_amount': 'Не хватает ингредиентов'})
        else:
            raise ValidationError({
                'ingredients_existence': 'Ингредиенты отсутствуют'})
        return data

    def validate_tags(self, data):
        if data:
            tags = []
            for tag in data:
                if tag in tags:
                    raise ValidationError({
                        'tags_uniqueness': 'Тэги должны быть уникальными'})
                tags.append(tag)
        else:
            raise ValidationError({
                'tags_existence': 'Тэги отсутствуют'
            })
        return data

    @staticmethod
    def get_ingredients(recipe=None, ingredients=None):
        for ingredient in ingredients:
            RecipeIngredients.objects.bulk_create(
                [RecipeIngredients(
                    recipe=recipe,
                    ingredient=Ingredient.objects.get(id=ingredient['id']),
                    amount=ingredient['amount']
                )])

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tag')
        recipe = Recipe.objects.create(
            author=self.context.get('request').user,
            **validated_data)
        self.get_ingredients(recipe, ingredients)
        recipe.tags.set(tags)

        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tag')
        instance.ingredients.clear()
        instance.tags.clear()
        self.get_ingredients(instance, ingredients)
        instance.tags.set(tags)

        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return GetMyRecipeSerializer(instance, context=self.context).data


class FavouriteSerializer(ModelSerializer):
    '''Сериалайзер добавления в избранное'''

    class Meta:
        model = Favourite
        fields = ('user', 'recipe')

    def validate(self, data):
        if Favourite.objects.filter(
            user=data.get('user'),
            recipe=data.get('recipe')
        ).exists():
            raise IntegrityError('Рецепт уже добавлен в Избранное')
        return data

    def to_representation(self, instance):
        return GetMyRecipeSerializer(
            instance.recipe,
            context=self.context).data


class ShoppingCartSerializer(ModelSerializer):
    '''Сериалайзер добавления в корзину'''

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')

    def validate(self, data):
        if ShoppingCart.objects.filter(
            user=data.get('user'),
            recipe=data.get('recipe')
        ).exists():
            raise IntegrityError('Рецепт уже в корзине')
        return data

    def to_representation(self, instance):
        return GetMyRecipeSerializer(
            instance.recipe,
            context=self.context).data
