from django.contrib import admin

from users.models import Subscriptions, User


@admin.register(User)
class UsersAdmin(admin.ModelAdmin):
    list_display = ('username', 'full_name', 'email')
    list_filter = ('email', 'username',)
    ordering = ('pk',)


@admin.register(Subscriptions)
class SubscriptionsAdmin(admin.ModelAdmin):
    list_display = ('author', 'user', 'date_added')
    list_filter = ('date_added',)
    ordering = ('date_added',)