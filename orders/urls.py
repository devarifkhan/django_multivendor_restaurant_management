from django.urls import path
from . import views

urlpatterns = [
    path('place_order/', views.place_order, name='place_order'),
    path('payments/', views.payments, name='payments'),
    path('order_complete/', views.order_complete, name='order_complete'),

    # Stripe
    path('stripe_success/', views.stripe_success, name='stripe_success'),
    path('stripe_cancel/', views.stripe_cancel, name='stripe_cancel'),

    # SSLCommerz
    path('sslcommerz_success/', views.sslcommerz_success, name='sslcommerz_success'),
    path('sslcommerz_fail/', views.sslcommerz_fail, name='sslcommerz_fail'),
    path('sslcommerz_cancel/', views.sslcommerz_cancel, name='sslcommerz_cancel'),
    path('sslcommerz_ipn/', views.sslcommerz_ipn, name='sslcommerz_ipn'),
]