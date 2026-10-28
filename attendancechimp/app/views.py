from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation
from zoneinfo import ZoneInfo

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .models import StudentProfile, InstructorProfile


CDT = ZoneInfo("America/Chicago")


def time_view(request):
    """Return current Chicago time as HH:MM (24-hour), plain text."""
    now = datetime.now(tz=CDT)
    return HttpResponse(now.strftime("%H:%M"), content_type="text/plain")

@csrf_exempt
@require_POST
def createUser(request):
    email = request.POST.get('email')
    user_name = request.POST.get('user_name')
    password = request.POST.get('password')
    is_student = request.POST.get('is_student') in ('1', 'true')
    if User.objects.filter(email=email).exists():
        return HttpResponseBadRequest("Email is already in use--login or use another one.")
    user = User.objects.create_user(username=user_name, email=email, password=password)
    if is_student:
        StudentProfile.objects.create(user=user)
    else:
        InstructorProfile.objects.create(user=user)
    login(request, user)
    return HttpResponse("User created", status=200)

def index(request):
    current_time = datetime.now(ZoneInfo("America/Chicago")).strftime("%H:%M")
    return render(request, "app/index.html", {"current_time": current_time})

from django.views.decorators.http import require_GET

@require_GET
def new_user_form(request):
    return render(request, "app/new.html")

def _decimal_to_str(x: Decimal) -> str:
    """Format Decimal without scientific notation and without trailing zeros."""
    s = format(x, "f")
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return s


def sum_view(request: HttpRequest) -> HttpResponse:
    """Return n1 + n2 from query params as plain text."""
    n1_str = request.GET.get("n1", "0")
    n2_str = request.GET.get("n2", "0")

    try:
        val = Decimal(n1_str) + Decimal(n2_str)
    except (InvalidOperation, ValueError):
        return HttpResponse("Bad Request: n1 and n2 must be numbers", status=400, content_type="text/plain")

    return HttpResponse(_decimal_to_str(val), content_type="text/plain")
