from django.contrib.auth import get_user_model
from django.db import models

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
        return self.name


class Ingredient(models.Model):
    name = models.CharField('Название', max_length=255, unique=True)
    unit = models.CharField('Единица измерения', max_length=32)

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
    ingredients = models.ManyToManyField(
        Ingredient, 'ingrediets', verbose_name='Ингридиенты'
    )
    tag = models.ManyToManyField(
        Tag, 'recipe_tags', verbose_name='Тэги'
    )
    cooking_time = models.PositiveIntegerField(
        'Время приготовления (в минутах)'
        )
    # image = models.ImageField('Изображение', upload_to='recipes_image/')

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self) -> str:
        return self.title
