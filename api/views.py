from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail
from django.db.models import Avg
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.exceptions import ValidationError
from rest_framework.filters import SearchFilter
from rest_framework.generics import get_object_or_404
from rest_framework.mixins import (
    CreateModelMixin,
    ListModelMixin,
    DestroyModelMixin,
)
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from urllib.error import HTTPError

from .filters import TitleFilter
from .models import Review, Title, Category, Genre, User
from .permissions import (
    IsAdminOrModeratorOrOwnerOrReadOnly,
    IsAdmin,
    IsAdminOrReadOnly,
)
from .serializers import (
    ReviewSerializer,
    CategorySerializer,
    CommentSerializer,
    TitleMasterSerializer,
    TitleListSerializer,
    GenreSerializer,
    UserSerializer,
    GetTokenSerializer,
    RegistrationSerializer,
)


@api_view(['POST'])
@permission_classes([AllowAny])
def get_token(request):
    """Получение JWT-токена"""
    serializer = GetTokenSerializer(data=request.data)
    if not serializer.is_valid():
        raise ValidationError(serializer.errors)
    user = get_object_or_404(
        User,
        email=serializer.validated_data['email'],
        confirmation_code=serializer.validated_data['confirmation_code'])
    refresh_tokens = RefreshToken.for_user(user)
    tokens = {
        'refresh': str(refresh_tokens),
        'access': str(refresh_tokens.access_token),
    }
    return Response({'message': tokens.items()})


@api_view(['POST'])
@permission_classes([AllowAny])
def registration(request):
    """Регистрация пользователя и получение confirmation_code"""
    serializer = RegistrationSerializer(data=request.data)
    if not serializer.is_valid():
        raise ValidationError(serializer.errors)
    email = serializer.validated_data['email']
    username = serializer.validated_data['username']
    if not email:
        return Response(
            {
                'message':
                    {
                        'Ошибка': 'Не указана почта для регистрации'
                    }
            },
            status=status.HTTP_403_FORBIDDEN
        )
    token = PasswordResetTokenGenerator()
    user = get_user_model()
    user.email = email
    user.last_login = timezone.now()
    user.password = ''
    confirmation_code = token.make_token(user)
    try:
        query_get, flag = get_user_model().objects.get_or_create(
            email=email,
            defaults={
                'username': username,
                'confirmation_code': confirmation_code,
                'last_login': timezone.now()})
        if not flag:
            return Response(
                {
                    'message':
                        {
                            'Ошибка': ('Пользователь с таким email '
                                       'уже существует.')
                        }
                },
                status=status.HTTP_403_FORBIDDEN
            )
    except HTTPError:
        return Response(
            {
                'message':
                    {
                        'Ошибка': 'Ошибка запроса'
                    }
            },
            status=status.HTTP_403_FORBIDDEN
        )
    send_mail(
        'Подтверждение адреса электронной почты yamdb',
        f'Вы получили это письмо, потому что регистрируетесь на ресурсе '
        f'yamdb Код подтверждения confirmation_code = '
        f'{confirmation_code}',
        settings.DEFAULT_FROM_EMAIL,
        [email, ],
        fail_silently=False,
    )
    return Response(
        {
            'message':
                {
                    'ОК': f'Пользователь c email {email} успешно создан. '
                          'Код подтверждения отправлен на электронную почту'
                }
        }
    )


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('-id', 'role')
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    lookup_field = 'username'

    @action(
        methods=['get', 'patch'],
        detail=False,
        permission_classes=[IsAuthenticated],
        url_path='me'
    )
    def me(self, request):
        serializer = UserSerializer(request.user, many=False)
        if request.method == 'PATCH':
            serializer = UserSerializer(
                request.user, data=request.data, partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


class TitleViewSet(viewsets.ModelViewSet):
    queryset = (
        Title.objects.annotate(rating=Avg('reviews__score')).order_by('-id')
    )
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = (DjangoFilterBackend, SearchFilter)
    filterset_class = TitleFilter

    def get_serializer_class(self):
        if self.action in (
                'create',
                'update',
                'partial_update'
        ):
            return TitleMasterSerializer
        return TitleListSerializer


class CrudToCategoryGenreViewSet(CreateModelMixin,
                                 ListModelMixin,
                                 DestroyModelMixin,
                                 viewsets.GenericViewSet):
    pass


class CategoryViewSet(CrudToCategoryGenreViewSet):
    queryset = Category.objects.all().order_by('-id')
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [SearchFilter]
    search_fields = ['name', ]
    lookup_field = 'slug'


class GenreViewSet(CrudToCategoryGenreViewSet):
    queryset = Genre.objects.all().order_by('-id')
    serializer_class = GenreSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [SearchFilter]
    search_fields = ['name', ]
    lookup_field = 'slug'


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [IsAdminOrModeratorOrOwnerOrReadOnly]

    def get_queryset(self):
        title = get_object_or_404(
            Title, id=self.kwargs.get('title_id')
        )
        return title.reviews.all()

    def perform_create(self, serializer):
        title = get_object_or_404(
            Title, id=self.kwargs.get('title_id')
        )
        serializer.save(title=title, author=self.request.user)


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [IsAdminOrModeratorOrOwnerOrReadOnly]

    def get_queryset(self):
        review = get_object_or_404(
            Review,
            id=self.kwargs.get('review_id'),
            title__id=self.kwargs.get('title_id'),
        )
        return review.comments.all()

    def perform_create(self, serializer):
        review = get_object_or_404(
            Review,
            id=self.kwargs.get('review_id'),
            title__id=self.kwargs.get('title_id'),
        )
        serializer.save(review=review, author=self.request.user)
