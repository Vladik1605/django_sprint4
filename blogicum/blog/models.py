"""Models for blog app (not used in the exercise)."""
from django.db import models
from core import models as published
from django.contrib.auth import get_user_model


User = get_user_model()


class Category(published.PublishedModel):
    title = models.CharField(max_length=256, blank=False,
                             verbose_name='Заголовок'
                             )
    description = models.TextField(blank=False, verbose_name='Описание')
    slug = models.SlugField(unique=True, blank=False,
                            verbose_name='Идентификатор',
                            help_text='Идентификатор страницы для URL; '
                            'разрешены символы латиницы, цифры, дефис'
                            ' и подчёркивание.'
                            )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'Категории'


class Location(published.PublishedModel):
    name = models.CharField(max_length=256, blank=False,
                            verbose_name='Название места'
                            )

    class Meta:
        verbose_name = 'местоположение'
        verbose_name_plural = 'Местоположения'


class Post(published.PublishedModel):
    title = models.CharField(max_length=256, blank=False,
                             verbose_name='Заголовок'
                             )
    text = models.TextField(blank=False, verbose_name='Текст')
    pub_date = models.DateTimeField(blank=False,
                                    verbose_name='Дата и время публикации',
                                    help_text='Если установить дату и время в '
                                    'будущем — можно делать отложенные '
                                    'публикации.'
                                    )
    author = models.ForeignKey(User, on_delete=models.CASCADE, blank=False,
                               verbose_name='Автор публикации'
                               )
    location = models.ForeignKey(Location,
                                 on_delete=models.SET_NULL,
                                 blank=True,
                                 null=True,
                                 verbose_name='Местоположение'
                                 )
    category = models.ForeignKey(Category, on_delete=models.SET_NULL,
                                 blank=False,
                                 null=True,
                                 verbose_name='Категория'
                                 )
    image = models.ImageField(upload_to='posts/', blank=True, null=True,
                              verbose_name='Изображение')

    class Meta:
        verbose_name = 'публикация'
        verbose_name_plural = 'Публикации'


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE,
                             related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField(blank=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'комментарий'
        verbose_name_plural = 'Комментарии'
