from django.urls import path, include
from . import views

urlpatterns = [
    path("ssl_payment", views.ssl_payment, name="ssl_payment"),
    path("place_order", views.place_order, name="place_order"),
    path("payment_success", views.payment_success, name="payment_success"),
    path("payment_validate", views.payment_validate, name="payment_validate"),
    path("order_complete", views.order_complete, name="order_complete"),
   
]
