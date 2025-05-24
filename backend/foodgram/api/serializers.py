from djoser.serializers import (
    UserCreateSerializer as DjoserUserCreateSerializer)
from djoser.serializers import UserSerializer as DjoserUserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from rest_framework.fields import ReadOnlyField

from recipes.models import (
    Favorite, Ingredient, Recipe, RecipeIngredient, ShoppingCart
)
from users.models import Subscription, User


class UserSerializer(DjoserUserSerializer):
    '''Класс-сериализатор пользователя'''
    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False)

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name',
            'is_subscribed', 'avatar'
        )

    def get_is_subscribed(self, obj):
        '''Метод проверки подписки пользователя на автора'''
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return Subscription.objects.filter(
            user=request.user, author=obj
        ).exists()


class UserCreateSerializer(DjoserUserCreateSerializer):
    '''Класс-сериализатор для создания пользователя'''
    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name', 'password'
        )


class SubscribeSerializer(UserSerializer):
    '''Класс-сериализатор совершения подписки на автора'''
    recipes = serializers.SerializerMethodField()
    recipes_count = ReadOnlyField(source='recipes.count')

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count', 'avatar'
        )

    def get_recipes(self, obj):
        '''Метод получение рецептов от автора'''
        request = self.context.get('request')
        recipes_limit = request.GET.get('recipes_limit')
        recipes = obj.recipes.all()
        if recipes_limit:
            recipes = recipes[:int(recipes_limit)]
        return RecipeShortSerializer(recipes, many=True,
                                     context=self.context).data


class SubscriptionSerializer(serializers.ModelSerializer):
    '''Класс-сериализатор подписок пользователя'''
    class Meta:
        model = Subscription
        fields = ('user', 'author')
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=('user', 'author'),
                message='Вы уже подписаны на этого автора'
            )
        ]

    def validate(self, data):
        '''Метод валидации подписок'''
        if data['user'] == data['author']:
            raise serializers.ValidationError('Нельзя'
                                              ' подписаться на самого себя')
        return data


class FavoriteSerializer(serializers.ModelSerializer):
    '''Класс-сериализатор для избранных рецептов'''
    class Meta:
        model = Favorite
        fields = ('user', 'recipe')
        validators = [
            UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже добавлен в избранное'
            )
        ]

    def to_representation(self, instance):
        '''Преобразует объект Favorite в
        представление RecipeShortSerializer'''
        return RecipeShortSerializer(
            instance.recipe,
            context={'request': self.context.get('request')}
        ).data


class ShoppingCartSerializer(serializers.ModelSerializer):
    '''Класс-сериализатор для списка покупок'''
    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')
        validators = [
            UniqueTogetherValidator(
                queryset=ShoppingCart.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже добавлен в список покупок'
            )
        ]

    def to_representation(self, instance):
        '''Метод преобразования ShoppingCart в
        представление RecipeShortSerializer'''
        return RecipeShortSerializer(
            instance.recipe,
            context={'request': self.context.get('request')}
        ).data


class IngredientSerializer(serializers.ModelSerializer):
    '''Класс-сериализатор для ингредиентов'''
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    '''Класс-сериализатор для ингредиентов в рецепте'''
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeIngredientCreateSerializer(serializers.ModelSerializer):
    '''Класс-сриализатор для добавления ингредиентов в рецепте'''
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    '''Класс-сериализатор для рецептов'''
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        many=True, read_only=True, source='recipe_ingredients'
    )
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time'
        )

    def get_is_favorited(self, obj):
        '''Метод проверки факта добавления рецепта в избранное'''
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return Favorite.objects.filter(
            user=request.user, recipe=obj
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        '''Метод проверки факта добавления рецепт в список покупок'''
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return ShoppingCart.objects.filter(
            user=request.user, recipe=obj
        ).exists()


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    '''Класс-сериализатор для создания и обновления рецептов.'''
    ingredients = RecipeIngredientCreateSerializer(many=True)
    image = Base64ImageField(required=True)
    author = UserSerializer(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id', 'ingredients', 'author',
            'name', 'image', 'text', 'cooking_time'
        )

    def validate(self, data):
        '''Проверяет валидность данных.'''
        ingredients = self.initial_data.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError(
                'Необходимо указать хотя бы один ингредиент'
            )

        ingredients_list = []
        for ingredient in ingredients:
            if int(ingredient['amount']) <= 0:
                raise serializers.ValidationError(
                    'Количество ингредиента должно быть больше 0'
                )
            ingredients_list.append(ingredient['id'])
        if len(ingredients_list) != len(set(ingredients_list)):
            raise serializers.ValidationError(
                'Ингредиенты не должны повторяться'
            )
        if int(data['cooking_time']) <= 0:
            raise serializers.ValidationError(
                'Время приготовления должно быть больше 0'
            )

        return data

    def validate_image(self, image):
        """Функция валидации картинки."""
        if not image:
            raise serializers.ValidationError('Картинка не может быть пустой')
        return image

    def create_ingredients(self, ingredients, recipe):
        '''Метод создания ингредиентов
        для рецепта.'''
        recipe_ingredients = []
        for ingredient in ingredients:
            recipe_ingredients.append(
                RecipeIngredient(
                    recipe=recipe,
                    ingredient=ingredient['id'],
                    amount=ingredient['amount']
                )
            )
        RecipeIngredient.objects.bulk_create(recipe_ingredients)

    def create(self, validated_data):
        '''Метод создания рецепта'''
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(
            author=self.context.get('request').user,
            **validated_data
        )
        self.create_ingredients(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        '''Метод обновления рецепта'''
        ingredients = validated_data.pop('ingredients')
        # Обновление основных полей
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time
        )
        if 'image' in validated_data:
            instance.image = validated_data.get('image')
        # Обновление ингредиентов
        instance.ingredients.clear()
        self.create_ingredients(ingredients, instance)
        instance.save()
        return instance

    def to_representation(self, instance):
        '''Метод преобразование объект Recipe
        в представление RecipeSerializer.'''
        return RecipeSerializer(
            instance,
            context={'request': self.context.get('request')}
        ).data


class RecipeShortSerializer(serializers.ModelSerializer):
    '''Класс-сериализатор для краткого представления рецепта'''
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
