from django.urls import path

from payments import views

app_name = "payments"

urlpatterns = [
    path("pricing/", views.pricing, name="pricing"),
    path("checkout/<slug:slug>/", views.checkout, name="checkout"),
    path("history/", views.history, name="history"),
]
