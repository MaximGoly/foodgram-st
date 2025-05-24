from django.contrib import admin
from django.utils.safestring import mark_safe

from .models import (
    Favorite, Ingredient, Recipe, RecipeIngredient, ShoppingCart
)


class RecipeIngredientInline(admin.TabularInline):
    '''Вложенная модель ингредиентов в рецепте.'''
    model = RecipeIngredient
    min_num = 1
    extra = 0


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    '''Панель управления рецептами.'''
    list_display = (
        'id', 'name', 'author', 'pub_date', 'get_favorite_count', 'get_image'
    )
    search_fields = ('name', 'author__username')
    list_filter = ('author', 'name')
    readonly_fields = ('get_favorite_count',)
    inlines = (RecipeIngredientInline,)

    @admin.display(description='В избранном')
    def get_favorite_count(self, obj):
        '''Получает число добавлений рецепта в избранное.'''
        return obj.in_favorites.count()

    @admin.display(description='Изображение')
    def get_image(self, obj):
        '''Получает HTML-код для отображения картинки в админке.'''
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" width="80">')
        return 'Нет изображения'


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    '''Панель управления ингредиентами.'''
    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('measurement_unit',)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    '''Панель управления избранными рецептами.'''
    list_display = ('id', 'user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
    list_filter = ('user', 'recipe')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    '''Панель управления списком покупок.'''
    list_display = ('id', 'user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
    list_filter = ('user', 'recipe')
