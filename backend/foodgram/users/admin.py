from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User, Subscription


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    '''Панель управления пользователями'''
    list_display = (
        'id', 'username', 'email', 'first_name', 'last_name',
        'is_active', 'is_staff'
    )
    list_filter = ('is_active', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email')
    ordering = ('username',)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    '''Панель управления подписками'''
    list_display = ('id', 'user', 'author')
    list_filter = ('user', 'author')
    search_fields = ('user__username', 'author__username')
