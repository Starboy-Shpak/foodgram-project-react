from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import UniqueConstraint

User = get_user_model()


class Tag(models.Model):
    name = models.CharField('Наименование', max_length=64, unique=True)
    color = models.CharField(u'Цвет', max_length=7,
                             help_text=(u'HEX color, as #RRGGBB'), unique=True)
    slug = models.SlugField('slug', max_length=64, unique=True)

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'
        ordering = ('slug',)

    def __str__(self) -> str:
        return f'{self.name} (цвет: {self.color})'


class Ingredient(models.Model):
    name = models.CharField('Название', max_length=255, unique=True)
    measurement_unit = models.CharField('Единица измерения', max_length=32)

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name',)

    def __str__(self) -> str:
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(
        User, models.CASCADE, 'author_recipes',
        verbose_name='Автор'
    )
    title = models.CharField('Название рецепта', max_length=255,)
    discription = models.TextField('Описание')
    pub_date = models.DateField(
        'Дата публикации', auto_now_add=True, editable=False
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        'ingredients',
        verbose_name='Ингредиенты',
        through='AmountIngredient',
    )
    tag = models.ManyToManyField(
        Tag, 'recipe_tags', verbose_name='Тэги'
    )
    cooking_time = models.PositiveIntegerField(
        'Время приготовления (в минутах)'
    )
    image = models.ImageField('Изображение', upload_to='recipes_image/')

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('title',)

    def __str__(self) -> str:
        return self.title


class AmountIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe, models.CASCADE, 'in_recipes', verbose_name='В каких рецептах',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        models.CASCADE,
        'used_ingredients',
        verbose_name='ингредиенты',
    )
    amount = models.PositiveIntegerField('Количество')

    class Meta:
        verbose_name = 'Количество ингредиента'
        verbose_name_plural = 'Количество ингредиентов'
        ordering = ('recipe',)
        constraints = (
            UniqueConstraint(
                fields=('recipe', 'ingredient', ),
                name='unique_ingredient',
            ),
        )

    def __str__(self) -> str:
        return f'{self.amount} {self.ingredient}'


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE, related_name='favorites',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='favorites',
        verbose_name='Рецепт'
    )

    class Meta:
        verbose_name = 'Избранное'
        constraints = [
            UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite_recipe'
            )
        ]

    def __str__(self):
        return f'{self.user} добавил в избранное "{self.recipe}"'


class ShoppingList(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='shopping_cart',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='shopping_cart',
        verbose_name='Рецепт'
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Список покупок'
        constraints = [
            UniqueConstraint(
                fields=['user', 'recipe'], name='unique_shopping_cart'
            )
        ]

    def __str__(self):
        return f'{self.user} добавил "{self.recipe}" в список покупок'
