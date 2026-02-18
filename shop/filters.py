import django_filters
from .models import Good, Tag, Type, Company
from django import forms


class GoodFilter(django_filters.FilterSet):
    cost = django_filters.RangeFilter(
        label="Диапазон цены"
    )

    tag = django_filters.ModelChoiceFilter(
        queryset=Tag.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        label="Теги",
        error_messages={
            "invalid_choice": "Выбранный тег не найден"
        }
    )

    type = django_filters.ModelChoiceFilter(
        queryset=Type.objects.all(),
        empty_label="Все типы",
        widget=forms.RadioSelect,
        label="Тип компонента",
        error_messages={
            "invalid_choice": "Категория не найдена"
        },
    )

    company = django_filters.ModelChoiceFilter(
        queryset=Company.objects.all(),
        empty_label="Все производители",
        widget=forms.RadioSelect,
        label="Производитель",
        error_messages={
            "invalid_choice": "Производитель не найден"
        }
    )

    name = django_filters.CharFilter(
        lookup_expr="icontains",
        label="Название",
        widget=forms.TextInput(attrs={
            "placeholder": "Введите название..."
        })
    )

    class Meta:
        model = Good
        fields = {
            'type': ['exact'],
            'company': ['exact'],
            'name': ['icontains'],
        }
