from django.urls import path
from .views import BankDetailsListCreateAPIView, BankDetailsRetrieveUpdateDestroyAPIView

urlpatterns = [
    path("bank-details/", BankDetailsListCreateAPIView.as_view(), name="bankdetails-list-create"),
    path("bank-details/<int:pk>/", BankDetailsRetrieveUpdateDestroyAPIView.as_view(), name="bankdetails-rud"),
]
