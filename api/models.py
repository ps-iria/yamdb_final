from django.db import models
from django.db.models import UniqueConstraint
from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator

from .validators import year_validator


class UserRoles(models.TextChoices):
    USER = 'user'
    MODERATOR = 'moderator'
    ADMIN = 'admin'


class User(AbstractUser):
    role = models.CharField(
        max_length=10,
        choices=UserRoles.choices,
        default=UserRoles.USER,
        verbose_name='Роль пользователя',
    )
    email = models.EmailField(
        max_length=128,
        blank=False,
        unique=True,
        verbose_name='Адрес электронной почты',
        db_index=True,
    )
    username = models.CharField(
        max_length=30,
        unique=True,
        blank=False,
        verbose_name='Логин',
    )
    first_name = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        verbose_name='Имя',
    )
    last_name = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        verbose_name='Фамилия',
    )
    bio = models.TextField(
        max_length=500,
        blank=True,
        verbose_name='О себе',
    )
    confirmation_code = models.CharField(
        max_length=255,
        unique=True,
        editable=False,
        null=True,
        blank=True
    )

    @property
    def is_admin(self):
        return self.role == UserRoles.ADMIN or self.is_superuser

    @property
    def is_moderator(self):
        return self.role == UserRoles.MODERATOR

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


class Category(models.Model):
    name = models.CharField(
        max_length=250,
        verbose_name='Категория',
        unique=True,
    )
    slug = models.SlugField(
        max_length=100,
        unique=True,
    )

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.name


class Genre(models.Model):
    name = models.CharField(
        max_length=250,
        verbose_name='Жанр',
        unique=True,
    )
    slug = models.SlugField(
        max_length=50,
        unique=True,
    )

    class Meta:
        verbose_name = 'Жанр'
        verbose_name_plural = 'Жанры'

    def __str__(self):
        return self.name


class Title(models.Model):
    name = models.CharField(max_length=250, verbose_name='Произведение')
    year = models.IntegerField(
        validators=[year_validator],
        null=True,
        blank=True,
        verbose_name='Год издания'
    )
    description = models.CharField(
        max_length=700,
        blank=True,
        verbose_name='Описание'
    )
    genre = models.ManyToManyField(
        Genre,
        related_name='titles',

    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name='Категория',
        related_name='titles')

    class Meta:
        verbose_name = 'Произведение'
        verbose_name_plural = 'Произведения'

    def list_genres(self):
        return self.genre.values_list('name')

    def __str__(self):
        return (f' name: {self.name},'
                f' year: {self.year},'
                f' genre: {self.list_genres()},'
                f' category: {self.category},'
                )


class Review(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Автор',
    )
    title = models.ForeignKey(
        Title,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Произведение, Категория, Жанр',
    )
    text = models.TextField(verbose_name='Отзыв', )
    score = models.IntegerField(
        'review score',
        validators=[
            MinValueValidator(1, message='Рейтинг не может быть меньше 1'),
            MaxValueValidator(10, message='Рейтинг не может быть больше 10')
        ]
    )
    pub_date = models.DateTimeField('Дата публикации', auto_now_add=True)

    class Meta:
        constraints = [
            UniqueConstraint(fields=['title', 'author'], name='unique_review')
        ]
        ordering = ['-pub_date']
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'

    def __str__(self):
        return self.text


class Comment(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
    )
    text = models.TextField()
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name='comments',
    )
    pub_date = models.DateTimeField('Дата создания', auto_now_add=True)

    class Meta:
        ordering = ['-pub_date']
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'

    def __str__(self):
        return self.text
