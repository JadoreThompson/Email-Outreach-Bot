from django.urls import path

from . import app

urlpatterns = [
    path("", app.index, name="index"),
]