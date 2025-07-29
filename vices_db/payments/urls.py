# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('create-subscription/', views.create_subscription, name='create_subscription'),
    path('stripe-webhook/', views.stripe_webhook, name='stripe_webhook'),
    path('handle-successful-subscription-payment/', views.handle_successful_subscription_payment, name='handle_successful_subscription_payment'),
    path('handle-failed-subscription-payment/', views.handle_failed_subscription_payment, name='handle_failed_subscription_payment'),
    path('handle-cancelled-subscription/', views.handle_subscription_cancelled, name='handle_cancelled_subscription'),
    path('handle-updated-subscription/', views.handle_subscription_updated, name='handle_updated_subscription'),
    path('subscription-status/<int:user_id>/', views.get_subscription_status, name='get_subscription_status'),
    path('cancel-subscription/', views.cancel_subscription, name='cancel_subscription'),
    path('reactivate-subscription/', views.reactivate_subscription, name='reactivate_subscription'),
]