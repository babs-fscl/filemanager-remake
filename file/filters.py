import django_filters
from .models import Document


class DocumentFilter(django_filters.FilterSet):
    company_name = django_filters.CharFilter(field_name='user__company_name', lookup_expr='icontains')
    file_name = django_filters.CharFilter(field_name='name', lookup_expr='icontains')

    class Meta:
        model = Document
        fields = ['company_name', 'file_name']
