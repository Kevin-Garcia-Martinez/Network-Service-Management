from django.contrib import admin
from django.urls import path, re_path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # Applications urls
    re_path('', include('applications.vlan.urls')),
]
