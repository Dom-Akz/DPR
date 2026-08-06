from django.contrib import admin
from django.urls import path
from dashboard import views


urlpatterns = [
    path("", views.login_u, name="login"),
    path("admin/login/", views.login_u, name="login"),
    path("admin/logout/", views.logout_u, name="logout"),
    path("admin/dashboard/", views.dashboard, name="dashboard"),
    path("admin/dashbaord/kpi/", views.kpi_list, name="kpi_list"),
    path("admin/dashboard/kpi/<int:pk>/", views.kpi_detail, name="kpi_detail"),
    path(
        "admin/dashboard/kpi/by-solution/",
        views.kpi_list_by_solution,
        name="kpi_by_solution",
    ),
    path("admin/dashboard/kri/", views.kri_list, name="kri_list"),
    path("admin/dashboard/kri/<int:pk>/", views.kri_detail, name="kri_detail"),
    path("admin/dashboard/profile/", views.user_profile, name="profile"),
    path(
        "api/indicator/<str:indicator_type>/<int:pk>/update/",
        views.api_update_indicator,
        name="api_update_indicator",
    ),
]
