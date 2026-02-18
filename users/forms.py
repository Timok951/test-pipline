from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import User, Role, UserPreference, UserCredenetials


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Имя пользователя",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    password = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )


class RegistrationForm(forms.ModelForm):
    password = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput
    )

    class Meta:
        model = User
        fields = ('username', 'password')
        labels = {
            'username': 'Имя пользователя',
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])

        role = Role.objects.get(rolename="CUSTOMER")
        user.role = role

        if commit:
            user.save()
        return user


class UserSettingsForm(forms.ModelForm):
    class Meta:
        model = UserPreference
        fields = ("theme", "date_format", "page_size", "saved_filters")
        labels = {
            "theme": "Тема оформления",
            "date_format": "Формат даты",
            "page_size": "Количество элементов на странице",
            "saved_filters": "Сохранённые фильтры",
        }
        widgets = {
            "saved_filters": forms.Textarea(attrs={"rows": 3}),
        }


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("email",)
        labels = {
            "email": "Электронная почта",
        }


class UserCredentialsForm(forms.ModelForm):
    class Meta:
        model = UserCredenetials
        fields = ("humanname", "phonenumber")
        labels = {
            "humanname": "ФИО",
            "phonenumber": "Номер телефона",
        }
