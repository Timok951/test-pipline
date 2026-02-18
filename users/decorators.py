from functools import wraps
from django.conf import settings
from django.http import HttpResponseForbidden
from django.shortcuts import redirect

ROLE_ALIASES = {
    "admin": {"admin", "administrator", "админ", "администратор"},
    "warehouse": {"warehouse", "storekeeper", "кладовщик", "складчик"},
    "customer": {"customer", "user", "пользователь", "клиент"},
}


def _normalize_role(role_name):
    if not role_name:
        return ""
    role_name = role_name.strip().lower()
    for key, aliases in ROLE_ALIASES.items():
        if role_name in aliases:
            return key
    return role_name


def role_required(*roles):
    role_set = {r.strip().lower() for r in roles if r}

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            user = request.user
            if not user.is_authenticated:
                return redirect(settings.LOGIN_URL)

            if user.is_superuser or user.is_staff:
                if "admin" in role_set:
                    return view_func(request, *args, **kwargs)

            role_name = ""
            if getattr(user, "role", None):
                role_name = user.role.rolename
            role_name = _normalize_role(role_name)

            if role_name in role_set:
                return view_func(request, *args, **kwargs)

            return HttpResponseForbidden("Forbidden")

        return _wrapped

    return decorator
