from django.contrib import admin
from django.contrib.admin import TabularInline

from foodgram.models import Recipe, Tag, Ingredient, AmountIngredient


##############################
# INLINES
##############################
class IngredientInline(TabularInline):
    model = AmountIngredient
    extra = 2


##############################
# MODELS
##############################
@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('title', 'author')
    list_filter = ('author', 'title', 'tag')
    inlines = (IngredientInline,)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'slug')


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    list_filter = ('name',)
