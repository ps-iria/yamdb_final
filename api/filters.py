import django_filters as filters

from .models import Title


class TitleFilter(filters.FilterSet):
    category = filters.CharFilter(
        field_name='category__slug', lookup_expr='exact',
    )
    genre = filters.CharFilter(
        field_name='genre__slug', lookup_expr='exact',
    )
    name = filters.CharFilter(
        field_name='name', lookup_expr='icontains',
    )

    class Meta:
        model = Title
        fields = ['name', 'category', 'genre', 'year']
