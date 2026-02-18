from django import forms
from .models import Type, Good, Rate


class GoodForm(forms.ModelForm):
    class Meta:
        model = Good
        fields = [
            "name",
            "amount",
            "cost",
            "image",
            "max_voltage",
            "capacity",
            "resistance",
            "article",
            "type",
            "company",
            "tag",
        ]
        labels = {
            "name": "Название",
            "amount": "Количество на складе",
            "cost": "Цена",
            "image": "Изображение",
            "max_voltage": "Максимальное напряжение (В)",
            "capacity": "Ёмкость",
            "resistance": "Сопротивление (Ом)",
            "article": "Статья",
            "type": "Тип компонента",
            "company": "Производитель",
            "tag": "Теги",
        }


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Rate
        fields = ["rating", "comment"]
        labels = {
            "rating": "Оценка",
            "comment": "Комментарий",
        }
