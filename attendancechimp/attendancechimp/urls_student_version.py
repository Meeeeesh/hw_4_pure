from django.contrib import admin
from django.urls import path

# TODO (HW2): wire up your endpoints:
#   /app/time
#   /app/sum
#
# You can either:
#  - import views directly and add paths here, OR
#  - include an app-level urls.py (optional)

urlpatterns = [
    path("admin/", admin.site.urls),
    # TODO: add your paths here
]
