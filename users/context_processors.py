def user_preferences(request):
    if not request.user.is_authenticated:
        return {"user_preference": None}
    preference = getattr(request.user, "preference", None)
    return {"user_preference": preference}
