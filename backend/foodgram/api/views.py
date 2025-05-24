from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError, NotAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
)
from rest_framework.response import Response
from djoser.views import UserViewSet as UserDjoserViewSet


from recipes.models import (
    Favorite, Ingredient, Recipe, RecipeIngredient, ShoppingCart
)
from users.models import Subscription, User
from .filters import IngredientFilter, RecipeFilter
from .pagination import CustomPagination
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    FavoriteSerializer, IngredientSerializer, RecipeCreateUpdateSerializer,
    RecipeSerializer, ShoppingCartSerializer, SubscribeSerializer,
    SubscriptionSerializer,
    UserSerializer,
)


class UserViewSet(UserDjoserViewSet):
    '''Вьюсет для работы с пользователями'''
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_permissions(self):
        """Переопределение разрешений для метода me"""
        if self.action == 'me':
            return [IsAuthenticated()]
        return super().get_permissions()

    @action(
        detail=False,
        methods=['get'],
        url_path='me'
    )
    def get_me(self, request):
        '''Метод получения текущего пользователя'''
        if not request.user.is_authenticated:
            raise NotAuthenticated()
        return Response(self.get_serializer(request.user).data)

    @action(
        detail=True,
        methods=['post', 'delete'],
        url_path='subscribe'
    )
    def subscribe(self, request, id=None):
        '''Метод подписки на автора'''
        author = get_object_or_404(User, pk=id)
        if request.method == 'POST':
            data = {'user': request.user.id, 'author': author.id}
            serializer = SubscriptionSerializer(
                data=data, context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                SubscribeSerializer(
                    author,
                    context={'request': request}
                ).data,
                status=status.HTTP_201_CREATED
            )

        subscription = Subscription.objects.filter(user=request.user,
                                                   author=author).first()
        if subscription is None:
            return Response({'detail': 'Подписки не существует'},
                            status=status.HTTP_400_BAD_REQUEST)
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        url_path='subscriptions',
    )
    def subscriptions(self, request):
        '''Метод просмотра подписок пользователя'''
        user = request.user
        subscription_queryset = user.subscriber.all().select_related('author')
        pages = self.paginate_queryset(subscription_queryset)
        authors_data = [subscription_queryset.author for subscription_queryset
                        in pages]
        serializer = SubscribeSerializer(
            authors_data,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=False,
        methods=['put', 'delete'],
        url_path='me/avatar',
    )
    def avatar(self, request):
        '''Метод редактирования аватара пользователя'''
        user = request.user
        if request.method == 'PUT':
            if 'avatar' not in request.data:
                raise ValidationError(
                    {'avatar': ['Это поле обязательно.']}
                )
            serializer = self.get_serializer(
                user, data=request.data,
                partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                {'avatar': serializer.data['avatar']},
                status=status.HTTP_200_OK
            )
        user.avatar.delete()
        user.save()
        return Response(
            {'message': 'Аватар удалён'},
            status=status.HTTP_204_NO_CONTENT
        )


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    '''Вьюсет для работы с ингредиентами'''
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class RecipeViewSet(viewsets.ModelViewSet):
    '''Вьюсет для работы с рецептами.'''
    queryset = Recipe.objects.all()
    pagination_class = CustomPagination
    permission_classes = (IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        '''Метод выбора сериализатора в зависимости от действий'''
        if self.request.method in ('POST', 'PUT', 'PATCH'):
            return RecipeCreateUpdateSerializer
        return RecipeSerializer

    @action(detail=True, methods=['get'], url_path='get-link',
            permission_classes=[AllowAny])
    def get_link(self, request, pk=None):
        '''Метод получения ссылки на рецепт'''
        recipe = self.get_object()
        path = f'/recipes/{recipe.pk}/'
        url = request.build_absolute_uri(path)
        return Response({'short-link': url}, status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk):
        '''Метод добавления и удаления рецепта из избранного'''
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)

        if request.method == 'POST':
            if Favorite.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {'errors': 'Рецепт уже добавлен в избранное'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            favorite = Favorite.objects.create(user=user, recipe=recipe)
            serializer = FavoriteSerializer(
                favorite, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            favorite = Favorite.objects.filter(user=user, recipe=recipe)
            if not favorite.exists():
                return Response(
                    {'errors': 'Рецепт не найден в избранном'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk):
        '''Метод добавления и удаления рецепта из списка покупок'''
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)

        if request.method == 'POST':
            if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {'errors': 'Рецепт уже добавлен в список покупок'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            cart = ShoppingCart.objects.create(user=user, recipe=recipe)
            serializer = ShoppingCartSerializer(
                cart, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            cart = ShoppingCart.objects.filter(user=user, recipe=recipe)
            if not cart.exists():
                return Response(
                    {'errors': 'Рецепт не найден в списке покупок'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            cart.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        '''Метод скачивания списка покупок PDF'''
        user = request.user
        ingredients = RecipeIngredient.objects.filter(
            recipe__in_shopping_cart__user=user
        ).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(
            amount=Sum('amount')
        ).order_by('ingredient__name')

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.pdf"'
        )

        # Создание PDF документа
        p = canvas.Canvas(response)

        # Регистрация шрифта для поддержки кириллицы
        pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))
        p.setFont('DejaVuSans', 14)

        # Заголовок документа
        p.drawString(200, 800, 'Список покупок')
        p.setFont('DejaVuSans', 12)
        # Отступы
        y_position = 750
        # Добавление ингредиентов в PDF
        for ingredient in ingredients:
            name = ingredient['ingredient__name']
            measurement_unit = ingredient['ingredient__measurement_unit']
            amount = ingredient['amount']
            p.drawString(
                50, y_position,
                f"{name} — {amount} {measurement_unit}"
            )
            y_position -= 25
            # Проверка, нужна ли новая страница
            if y_position <= 50:
                p.showPage()
                p.setFont('DejaVuSans', 12)
                y_position = 800
        p.showPage()
        p.save()
        return response
