from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect, render

from core.web.shared import User


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    error_message = ""
    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()
        password = request.POST.get("password") or ""
        user = authenticate(request, username=username, password=password)
        if user is None:
            error_message = "Invalid username or password."
        else:
            login(request, user)
            return redirect("dashboard")

    return render(
        request,
        "pages/login.html",
        {
            "meta_title": "Login",
            "active_page": "login",
            "topbar_context": "Login",
            "error_message": error_message,
        },
    )


def register_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    error_message = ""
    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()
        password = request.POST.get("password") or ""
        password_confirm = request.POST.get("password_confirm") or ""

        if not username:
            error_message = "Username is required."
        elif User.objects.filter(username=username).exists():
            error_message = "That username already exists."
        elif len(password) < 8:
            error_message = "The password must be at least 8 characters long."
        elif password != password_confirm:
            error_message = "Passwords do not match."
        else:
            user = User.objects.create_user(
                username=username,
                password=password,
                first_name=(request.POST.get("first_name") or "").strip(),
                last_name=(request.POST.get("last_name") or "").strip(),
                email=(request.POST.get("email") or "").strip(),
            )
            login(request, user)
            return redirect("dashboard")

    return render(
        request,
        "pages/register.html",
        {
            "meta_title": "Register",
            "active_page": "register",
            "topbar_context": "Register",
            "error_message": error_message,
        },
    )


def logout_view(request):
    logout(request)
    return redirect("login")
