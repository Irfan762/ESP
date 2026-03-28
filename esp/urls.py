"""
URL conf for the GSoC prototype.
Covers: auth, dashboard, scheduling grid page, and the AJAX endpoint.
"""
from django.urls import path
from django.contrib.auth import views as auth_views
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import json


# ── Scheduling grid view ──────────────────────────────────────────────────────
@login_required
def ajaxscheduling(request, program_url):
    """
    Renders the scheduling grid page.
    program_url is passed to the template for display only.
    The real ESP view does a lot more (loads sections, rooms, timeslots from DB).
    """
    return render(request, "scheduling/ajaxscheduling.html", {
        "program_url": program_url,
    })


# ── AJAX schedule endpoint ────────────────────────────────────────────────────
@csrf_exempt          # Playwright tests send the CSRF token via header; exempt for simplicity
@login_required
def ajax_schedule_class(request):
    """
    Stub AJAX endpoint that Playwright intercepts in the grid tests.
    In the real ESP this validates room availability and writes to the DB.
    In the prototype it just echoes success — Playwright mocks override it anyway.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        payload = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    section_id = payload.get("section_id")
    room       = payload.get("room")
    timeslot   = payload.get("timeslot")

    if not all([section_id, room, timeslot]):
        return JsonResponse({"error": "Missing fields"}, status=400)

    return JsonResponse({
        "status":  "success",
        "message": f"Section {section_id} scheduled in {room} at {timeslot}",
    })


urlpatterns = [
    # ── Auth ──
    path("myesp/login/", auth_views.LoginView.as_view(
        template_name="registration/login.html",
        next_page="/esp/",
    ), name="login"),
    path("myesp/logout/", auth_views.LogoutView.as_view(next_page="/myesp/login/"), name="logout"),

    # ── Dashboard ──
    path("esp/", lambda r: HttpResponse("<h1>ESP Dashboard</h1>"), name="esp_home"),

    # ── Scheduling grid  /manage/<org>/<program>/ajaxscheduling ──
    # Matches PROGRAM_URL = "mit_splash/2024" from the test file
    path("manage/<path:program_url>/ajaxscheduling", ajaxscheduling, name="ajaxscheduling"),

    # ── AJAX endpoint that Scheduler.js POSTs to ──
    path("ajax_schedule_class", ajax_schedule_class, name="ajax_schedule_class"),

    path("", lambda r: HttpResponse("ESP prototype"), name="home"),
]
