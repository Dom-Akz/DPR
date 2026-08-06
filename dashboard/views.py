from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from functools import wraps
from .models import Administrateur, Indicator, IndicatorMeasurement, Solution
from django.contrib import messages
from django_smart_ratelimit import ratelimit


# Authentification :
def login_view(request):
    if request.user.is_authenticated:
        return redirect("/admin/dashboard/")
    return render(request, "login.html")


@ratelimit(key="ip", rate="5/m", block=True)
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
            return redirect("/admin/dashboard/")
        else:
            messages.error(request, "Invalid username or password")
            return render(request, "login.html")

    return render(request, "login.html")


def logout_u(request):
    logout(request)
    request.session.flush()
    return redirect("/admin/login/")


# Dashboard


def niveau_required(allowed_niveaux=None):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect("login")

            # Superusers can access all levels
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            # Check if user's niveau is in allowed list
            if allowed_niveaux and request.user.niveau not in allowed_niveaux:
                return redirect("dashboard")

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


@login_required(login_url="login")
def dashboard(request):
    """Main dashboard view"""
    context = {
        "user": request.user,
    }

    # If superuser, show consolidated view
    if request.user.is_superuser or request.user.is_supperuser:
        context["is_superuser"] = True
        context["kpi_count"] = Indicator.objects.filter(kind="KPI").count()
        context["kri_count"] = Indicator.objects.filter(kind="KRI").count()
    else:
        # Regular users see only their role level
        context["kpi_count"] = Indicator.objects.filter(
            kind="KPI", level=request.user.role
        ).count()
        context["kri_count"] = Indicator.objects.filter(
            kind="KRI", level=request.user.role
        ).count()

    return render(request, "dashboard/index.html", context)


@login_required(login_url="login")
def kpi_list(request):
    """List KPIs - respects user role level"""
    if request.user.is_superuser or request.user.is_supperuser:
        # Superusers see consolidated view with all levels
        kpis_by_level = {}
        for level_code, level_name in Indicator.LEVEL_CHOICES:
            indicators = (
                Indicator.objects.filter(kind="KPI", level=level_code)
                .order_by("name")
                .prefetch_related("measurements")
            )
            # Enrich indicators with latest measurement data

        level_tabs = Indicator.LEVEL_CHOICES

        context = {
            "kpis_by_level": kpis_by_level,
            "level_tabs": level_tabs,
            "is_superuser": True,
            "selected_level": request.GET.get("level", "all"),
        }
    else:
        kpis = (
            Indicator.objects.filter(kind="KPI", level=request.user.role)
            .order_by("name")
            .prefetch_related("measurements")
        )

        context = {
            "kpis": kpis,
            "user_role": request.user.get_role_display()
            if request.user.role
            else "N/A",
        }

    return render(request, "dashboard/kpi.html", context)


@login_required(login_url="login")
def kri_list(request):
    """List KRIs - respects user role level"""
    if request.user.is_superuser or request.user.is_supperuser:
        # Superusers see consolidated view with all levels
        kris_by_level = {}
        for level_code, level_name in Indicator.LEVEL_CHOICES:
            indicators = (
                Indicator.objects.filter(kind="KRI", level=level_code)
                .order_by("name")
                .prefetch_related("measurements")
            )

            kris_by_level[level_code] = indicators

        level_tabs = Indicator.LEVEL_CHOICES

        context = {
            "kris_by_level": kris_by_level,
            "level_tabs": level_tabs,
            "is_superuser": True,
            "selected_level": request.GET.get("level", "all"),
        }
    else:
        kris = (
            Indicator.objects.filter(kind="KRI", level=request.user.role)
            .order_by("name")
            .prefetch_related("measurements")
        )
        context = {
            "kris": kris,
            "user_role": request.user.get_role_display()
            if request.user.role
            else "N/A",
        }

    return render(request, "dashboard/kri.html", context)


@login_required(login_url="login")
def kpi_detail(request, pk):
    """KPI detail view with history"""
    try:
        indicator = Indicator.objects.get(pk=pk, kind="KPI")

        # Check access control
        if not (request.user.is_superuser or request.user.is_supperuser):
            if indicator.level != request.user.role:
                return redirect("dashboard")

        # Get latest measurement for this indicator
        latest_measurement = (
            indicator.measurements.first() if indicator.measurements.exists() else None
        )

        context = {
            "indicator": indicator,
            "latest_measurement": latest_measurement,
            "measurements": indicator.measurements.all()[:10],
        }
        return render(request, "dashboard/kpi_detail.html", context)
    except Indicator.DoesNotExist:
        return redirect("/admin/dashboard/kpi_list")


@login_required(login_url="login")
def kri_detail(request, pk):
    """KRI detail view with history"""
    try:
        indicator = Indicator.objects.get(pk=pk, kind="KRI")

        # Check access control
        if not (request.user.is_superuser or request.user.is_supperuser):
            if indicator.level != request.user.role:
                return redirect("dashboard")

        # Get latest measurement for this indicator
        latest_measurement = (
            indicator.measurements.first() if indicator.measurements.exists() else None
        )

        context = {
            "indicator": indicator,
            "latest_measurement": latest_measurement,
            "measurements": indicator.measurements.all()[:10],
        }
        return render(request, "dashboard/kri_detail.html", context)
    except Indicator.DoesNotExist:
        return redirect("/admin/dashboard/kri_list")


@login_required(login_url="login")
def kpi_list_by_solution(request):
    """N0 KPIs grouped by solution"""
    if not (request.user.is_superuser or request.user.is_supperuser):
        # Only show N0 level KPIs for N0 users
        if request.user.role != "N0":
            return redirect("kpi_list")

    # Get all solutions with their N0 KPI indicators
    solutions = Solution.objects.prefetch_related("indicators").all()

    context = {
        "solutions": solutions,
    }
    return render(request, "dashboard/kpi_by_solution.html", context)


@login_required(login_url="login")
def user_profile(request):
    """User profile view"""
    context = {
        "user": request.user,
    }
    return render(request, "dashboard/profile.html", context)


@login_required(login_url="login")
@require_http_methods(["POST"])
def api_update_indicator(request, pk, indicator_type):
    """API endpoint to update indicator values (for future use)"""
    if not request.user.is_superuser:
        return JsonResponse({"error": "Unauthorized"}, status=403)

    try:
        if indicator_type == "kpi":
            indicator = KPI.objects.get(pk=pk)
        elif indicator_type == "kri":
            indicator = KRI.objects.get(pk=pk)
        else:
            return JsonResponse({"error": "Invalid indicator type"}, status=400)

        # Update logic would go here
        return JsonResponse({"success": True, "id": indicator.pk})
    except (KPI.DoesNotExist, KRI.DoesNotExist):
        return JsonResponse({"error": "Indicator not found"}, status=404)
