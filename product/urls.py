from django.urls import path
from .views import ProductCreateView, CheckoutView, InitiatePaymentView, PaymentResView, DodoWebhookView

urlpatterns = [
    path('create/', ProductCreateView.as_view(), name='product_create'),
    path('checkout/<int:product_id>/', CheckoutView.as_view(), name='checkout'),
    path('initiate_payment/<int:product_id>/', InitiatePaymentView.as_view(), name='initiate_payment'),
    path('payment/res/', PaymentResView.as_view(), name='payment_res'),
    path('payment/webhook/', DodoWebhookView.as_view(), name='payment_webhook'),

]