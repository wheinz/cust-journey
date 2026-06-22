from django.contrib import admin
from django.shortcuts import redirect
from django.urls import include, path


def home_redirect(request):
    return redirect('journey:home')


urlpatterns = [
    path('', home_redirect, name='home'),
    path('admin/', admin.site.urls),
    path('journey/', include('journey.urls')),
    path('kpi/', include('kpi.urls')),
]
