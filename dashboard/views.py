from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages


# Authentification :
def login_view(request):
    if request.user.is_authenticated:
        return redirect("/admin/dashboard")
    return render(request, "login.html")


def login_u(request):
    if request.user.is_authenticated:
        return redirect("/admin/dashboard/")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "You have been logged in successfully.")
            return redirect("admin/dashboard/")
        else:
            messages.error(request, "Invalid username or password")
            return render(request, "login.html")

    return render(request, "login.html")


def logout_u(request):
    logout(request)
    request.session.flush()
    return redirect("admin/login/")
