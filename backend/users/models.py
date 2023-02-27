from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import F, Q, UniqueConstraint


class User(AbstractUser):
    username = models.CharField(
        'Никнейм', max_length=64, unique=True, null=True, blank=True
    )
    email = models.EmailField(
        'Электронная почта',
        blank=False,
        unique=True,
        help_text='Обязательное поле'
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    def __str__(self):
        return self.username


class Subscriptions(models.Model):
    author = models.ForeignKey(
        User, models.CASCADE, 'author', verbose_name='Автор',
    )
    user = models.ForeignKey(
        User, models.CASCADE, 'follower', verbose_name='Подписчик',
    )
    date_added = models.DateField(
        'Дата подписки', auto_now_add=True, editable=False
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        ordering = ('date_added',)
        constraints = [
            UniqueConstraint(fields=('user', 'author'), name='unique_follow'),
            models.CheckConstraint(
                check=~Q(user=F('author')), name='no_self_follow'
            )
        ]

    def __str__(self):
        return f'{self.user.username} -> {self.author.username}'
