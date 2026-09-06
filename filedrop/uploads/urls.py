from django.urls import path

from . import views

app_name = "uploads"

urlpatterns = [
    path("f/<uuid:token>/", views.upload_view, name="upload"),
    path("f/<uuid:token>/uploaded/", views.upload_success_view, name="upload_success"),
    path("download/<int:pk>/", views.download_view, name="download"),
]
