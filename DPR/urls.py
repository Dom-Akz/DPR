from django.contrib import admin
from django.urls import path
from dashboard import views


urlpatterns = [
    path("", views.logout_u, name="login"),
    path("admin/login/", views.login_u, name="login"),
    path("admin/logout/", views.logout_u, name="logout"),
]
