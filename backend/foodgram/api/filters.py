from django_filters import rest_framework as filters

from recipes.models import Ingredient, Recipe


class IngredientFilter(filters.FilterSet):
    '''Класс фильтра для ингредиентов'''
    name = filters.CharFilter(
        field_name='name',
        # lookup_expr='icontains'
        lookup_expr='startswith'
    )

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(filters.FilterSet):
    '''Класс фильтра для рецептов'''
    is_favorited = filters.BooleanFilter(
        method='filter_is_favorited'
    )
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart'
    )
    author = filters.NumberFilter(
        field_name='author__id'
    )

    class Meta:
        model = Recipe
        fields = ('author', 'is_favorited', 'is_in_shopping_cart')

    def filter_is_favorited(self, queryset, name, value):
        '''Метод фильтрации рецептов по наличию их в избранных'''
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(in_favorites__user=user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        '''Метод фильтрации рецептов по наличию их в списке покупок'''
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(in_shopping_cart__user=user)
        return queryset
