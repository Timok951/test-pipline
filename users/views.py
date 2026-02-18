from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse_lazy
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from .forms import LoginForm, RegistrationForm, UserSettingsForm, UserProfileForm, UserCredentialsForm
from .metrics import login_counter, update_metrics
from users.services import AuthService
from .models import UserPreference, UserCredenetials

def login_user(request):
    form = LoginForm(data=request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            user = form.get_user()
            AuthService.login_user(request, user)
            return profile_page(request)
        
    return render(request, 'auth/login.html', {'form':form})

def registration_user(request):
    form = RegistrationForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            user = form.save()
            login(request, user)
            update_metrics()#update metrics 
            return redirect("/")
    return render(request, 'auth/register.html', {'form': form})

def logout_user(request):
    logout(request)
    return redirect('/')

def profile_page(request):
    return render(request, "profile/profile.html")


@login_required
def user_settings(request):
    preference, _ = UserPreference.objects.get_or_create(user=request.user)
    credentials, _ = UserCredenetials.objects.get_or_create(user=request.user)
    if request.method == "POST":
        form_type = request.POST.get("form_type")
        profile_form = UserProfileForm(request.POST, instance=request.user)
        credentials_form = UserCredentialsForm(request.POST, instance=credentials)
        preference_form = UserSettingsForm(request.POST, instance=preference)
        if form_type == "profile":
            if profile_form.is_valid() and credentials_form.is_valid():
                profile_form.save()
                credentials_form.save()
                messages.success(request, "Profile saved.")
                return redirect("user_settings")
        elif form_type == "preferences":
            if preference_form.is_valid():
                preference_form.save()
                messages.success(request, "Preferences saved.")
                return redirect("user_settings")
    else:
        profile_form = UserProfileForm(instance=request.user)
        credentials_form = UserCredentialsForm(instance=credentials)
        preference_form = UserSettingsForm(instance=preference)
    return render(
        request,
        "profile/settings.html",
        {
            "profile_form": profile_form,
            "credentials_form": credentials_form,
            "preference_form": preference_form,
        },
    )
            
