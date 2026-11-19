from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation
from zoneinfo import ZoneInfo

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .models import StudentProfile, InstructorProfile, getUploadsForCourse
from django.core.exceptions import ValidationError
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from .models import (Course, Lecture, QRCodeUpload, InstructorProfile,
                     StudentProfile, is_instructor, is_student)
from django.views.decorators.http import require_GET


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


@login_required
def new_course(request):
    """Show the form for creating a course."""
    return render(request, "app/new_course.html")


@login_required
def new_lecture(request):
    """Show the form for creating a lecture for the user's courses."""
    courses = Course.objects.filter(instructor=request.user)
    return render(request, "app/new_lecture.html", {"courses": courses})


@login_required
def new_qr_upload(request):
    """Show the form for uploading a QR code image."""
    return render(request, "app/new_qr_upload.html")


@csrf_exempt
def createCourse(request):
    """Create a Course from POST.
    """
    if not request.user.is_authenticated or not is_instructor(request.user):
        return HttpResponse("Unauthorized", status=401)
    if request.method != "POST":
        return HttpResponse("POST required", status=405)

    name = request.POST.get("course-name")
    if not name:
        return HttpResponse("course-name is required", status=400)
    if Course.objects.filter(name=name).exists():
        return HttpResponse("A course with that name already exists", status=400)

    try:
        Course.objects.create(
            name=name,
            instructor=request.user,
            start_time=request.POST.get("start-time") or None,
            end_time=request.POST.get("end-time") or None,
            day_mon="day-mon" in request.POST,
            day_tue="day-tue" in request.POST,
            day_wed="day-wed" in request.POST,
            day_thu="day-thu" in request.POST,
            day_fri="day-fri" in request.POST,
        )
    except ValidationError:
        return HttpResponse("Must be in format HH:MM", status=400)
    
    return HttpResponse("Course created")


@csrf_exempt
def createLecture(request):
    """Create a Lecture for the course for instructors only.
    """
    if not request.user.is_authenticated or not is_instructor(request.user):
        return HttpResponse("Unauthorized", status=401)
    if request.method != "POST":
        return HttpResponse("POST required", status=405)

    course = Course.objects.filter(name=request.POST.get("choice")).first()
    if course is None:
        return HttpResponse("Course not found", status=400)
    Lecture.objects.create(course=course)
    return HttpResponse("Lecture created")


@csrf_exempt
def createQRCodeUpload(request):
    """Save the POST for students only.
    """
    if not request.user.is_authenticated or not is_student(request.user):
        return HttpResponse("Unauthorized", status=401)
    if request.method != "POST":
        return HttpResponse("POST required", status=405)

    QRCodeUpload.objects.create(student=request.user,
                                image=request.FILES.get("imageUpload"))
    return HttpResponse("Upload saved")


def dumpUploads(request):
    """Return every QR code upload as JSON data
    """
    if not request.user.is_authenticated or not is_instructor(request.user):
        return HttpResponse("Unauthorized", status=401)

    data = [
        {
            "username": upload.student.username,
            "upload_time": timezone.localtime(upload.uploaded_at).strftime("%Y-%m-%d %H:%M:%S"),
        }
        for upload in QRCodeUpload.objects.all()
    ]
    return JsonResponse(data, safe=False)

def getUploads(request):
    """Return qr code uploads as JSON for each student's username, or return errors.
    """
    if not is_instructor(request.user):
        return HttpResponse("Unauthorized", status=401)

    course = request.GET.get("course")
    if not course:
        return JsonResponse({"error": "Missing course parameter"}, status=400)

    data = [
        {"username": upload.student.username,
         "upload_time": timezone.localtime(upload.uploaded_at).strftime("%Y-%m-%d %H:%M:%S"),
        }
        for upload in getUploadsForCourse(course)
    ]
    return JsonResponse(data, safe=False)