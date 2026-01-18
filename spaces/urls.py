from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("login/", views.login, name="login"),
    path("logout/", views.logout_page, name="logout"),
    path("register/", views.register, name="register"),
    path("rentals/", views.rentals, name="rentals"),
    path("rentals/<str:category>/", views.rentalsview, name="rentals_category"),
    path("booking/<int:space_id>/", views.booking, name="booking"),
    path(
        "process-payment/<int:booking_id>/",
        views.process_payment,
        name="process_payment",
    ),  #
    path("my-bookings/", views.my_bookings, name="my_bookings"),  #
    path("invoice/<int:booking_id>/", views.invoice, name="invoice"),  #
    path("payment/", views.payment, name="payment_new"),  #
    path("process-payment/", views.process_payment, name="process_payment"),  #
]
