from django.urls import path

from certificates import views

app_name = "certificates"

urlpatterns = [
    path("", views.my_certificates, name="my_certificates"),
    path("generate/<slug:slug>/", views.generate_certificate, name="generate"),
    path("verify/<uuid:certificate_id>/", views.verify, name="verify"),
    path("<uuid:certificate_id>/", views.certificate_detail, name="detail"),
]
