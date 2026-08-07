from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from functools import wraps
from .models import Administrateur, Indicator, IndicatorMeasurement, Solution
from django.contrib import messages
from django_smart_ratelimit import ratelimit
from .reporting import build_payload, export_report


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


def superuser_required(view):
    @wraps(view)
    @login_required(login_url="login")
    def wrapped(request, *args, **kwargs):
        if not request.user.is_superuser:
            return redirect("dashboard")
        return view(request, *args, **kwargs)

    return wrapped


@superuser_required
def admin_management(request):
    admins = Administrateur.objects.all().order_by("last_name", "first_name")
    edit_admin = None
    edit_id = request.GET.get("edit")
    if edit_id and edit_id.isdigit():
        edit_admin = Administrateur.objects.filter(pk=edit_id).first()
    return render(
        request,
        "dashboard/admin_management.html",
        {
            "admins": admins,
            "edit_admin": edit_admin,
            "roles": Administrateur.ROLE_CHOICES,
        },
    )


@superuser_required
def admin_create(request):
    if request.method == "POST":
        required = ["last_name", "first_name", "email", "role", "username"]
        if all(request.POST.get(field, "").strip() for field in required):
            Administrateur.objects.create_user(
                username=request.POST["username"].strip(),
                first_name=request.POST["first_name"].strip(),
                last_name=request.POST["last_name"].strip(),
                email=request.POST["email"].strip(),
                role=request.POST["role"].strip(),
                is_active=True,
            )
            messages.success(request, "Administrateur créé avec succès.")
        else:
            messages.error(
                request, "Tous les champs obligatoires doivent être renseignés."
            )
    return redirect("admin_management")


@superuser_required
def admin_update(request, pk):
    admin = get_object_or_404(Administrateur, pk=pk)
    if request.method == "POST":
        admin.last_name = request.POST.get("last_name", admin.last_name).strip()
        admin.first_name = request.POST.get("first_name", admin.first_name).strip()
        admin.email = request.POST.get("email", admin.email).strip()
        admin.username = request.POST.get("username", admin.username).strip()
        admin.role = request.POST.get("role", admin.role).strip()
        admin.save(update_fields=["nom", "prenom", "email", "role"])
        messages.success(request, "Administrateur mis à jour.")
    return redirect("admin_management")


@superuser_required
def admin_toggle(request, pk):
    admin = get_object_or_404(Administrateur, pk=pk)
    if request.method == "POST":
        admin.is_active = not admin.is_active
        admin.save(update_fields=["is_active"])
    return redirect("admin_management")


@superuser_required
def admin_delete(request, pk):
    if request.method == "POST":
        get_object_or_404(Administrateur, pk=pk).delete()
    return redirect("admin_management")


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


def is_solution_filter_allowed(user):
    return (
        user.is_superuser
        or getattr(user, "is_supperuser", False)
        or getattr(user, "role", None) == "N0"
    )


def admin_required(view):
    @wraps(view)
    @login_required(login_url="login")
    def wrapped(request, *args, **kwargs):
        if not (request.user.is_superuser or getattr(request.user, "role", None)):
            return redirect("dashboard")
        return view(request, *args, **kwargs)

    return wrapped


@admin_required
def report_builder(request):
    solutions = Solution.objects.all()
    qs = (
        Indicator.objects.select_related("solution")
        .prefetch_related("measurements")
        .order_by("kind", "level", "name")
    )
    params = request.POST if request.method == "POST" else request.GET
    kind = params.get("kind", "all")
    solution_id = params.get("solution", "all")
    can_filter_level = request.user.is_superuser
    level = params.get("level", "all")
    if kind in {"KPI", "KRI"}:
        qs = qs.filter(kind=kind)
    can_filter_solution = is_solution_filter_allowed(request.user)
    if can_filter_solution and solution_id != "all":
        qs = qs.filter(solution_id=solution_id)
    elif not can_filter_solution:
        solution_id = "all"
    if can_filter_level:
        if level != "all":
            qs = qs.filter(level=level)
    else:
        qs = qs.filter(level=request.user.role)
        level = request.user.role
    if request.method == "POST":
        selected = request.POST.getlist("indicators")
        selected_qs = qs.filter(pk__in=selected) if selected else qs
        title = (
            request.POST.get("title", "Rapport KPI / KRI").strip()
            or "Rapport KPI / KRI"
        )
        fmt = request.POST.get("format", "pdf")
        language = request.POST.get("language", "fr")
        payload = build_payload(
            selected_qs,
            title,
            kind if kind != "all" else "",
            solutions.filter(pk=solution_id).first().name
            if solution_id != "all" and solution_id.isdigit()
            else "",
            language=language,
        )
        return export_report(payload, fmt)
    return render(
        request,
        "dashboard/report_builder.html",
        {
            "indicators": qs,
            "solutions": solutions,
            "levels": Indicator.LEVEL_CHOICES,
            "kind": kind,
            "selected_solution": solution_id,
            "selected_level": level,
            "can_filter_solution": can_filter_solution,
            "can_filter_level": can_filter_level,
        },
    )


@login_required(login_url="login")
def indicator_list(request, kind):
    qs = (
        Indicator.objects.filter(kind=kind)
        .select_related("solution")
        .prefetch_related("measurements")
    )
    can_filter_solution = is_solution_filter_allowed(request.user)
    can_filter_level = request.user.is_superuser
    level = request.GET.get("level")
    solution_id = request.GET.get("solution")
    if can_filter_level:
        if level and level != "all":
            qs = qs.filter(level=level)
    else:
        # Non-superusers are always scoped to their assigned level. The
        # query-string value is intentionally ignored to prevent escalation.
        qs = qs.filter(level=request.user.role)
        level = request.user.role
    if can_filter_solution and solution_id and solution_id != "all":
        qs = qs.filter(solution_id=solution_id)
    return render(
        request,
        f"dashboard/{kind.lower()}.html",
        {
            "indicators": qs.order_by("level", "name"),
            "kind": kind,
            "solutions": Solution.objects.all(),
            "levels": Indicator.LEVEL_CHOICES,
            "selected_level": level or "all",
            "selected_solution": solution_id or "all",
            "can_filter_solution": can_filter_solution,
            "can_filter_level": can_filter_level,
        },
    )
