from django.urls import path

from payments import views

app_name = "payments"

urlpatterns = [
    path("pricing/", views.pricing, name="pricing"),
    path("checkout/<slug:slug>/", views.checkout, name="checkout"),
    path("success/<str:reference>/", views.success, name="success"),
    path("confirm/<str:reference>/", views.confirm, name="confirm"),
    path("invoices/<str:invoice_number>/", views.invoice, name="invoice"),
    path("invoices/<str:invoice_number>/download/", views.invoice_download, name="invoice_download"),
    path("history/", views.history, name="history"),
]
