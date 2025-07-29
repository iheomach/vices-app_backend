import stripe
import json
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth.models import User  # Adjust to your User model

stripe.api_key = settings.STRIPE_SECRET_KEY

@api_view(['POST'])
def create_subscription(request):
    try:
        data = request.data
        price_id = data.get('price_id')
        user_id = data.get('user_id')
        email = data.get('email')
        
        if not price_id or not email:
            return Response({'error': 'Missing required fields'}, status=400)
        
        # Check if customer already exists
        customers = stripe.Customer.list(email=email, limit=1)
        if customers.data:
            customer = customers.data[0]
            print(f"Found existing customer: {customer.id}")
        else:
            # Create new customer
            customer = stripe.Customer.create(
                email=email,
                metadata={'user_id': user_id}
            )
            print(f"Created new customer: {customer.id}")
        
        # Create subscription
        subscription = stripe.Subscription.create(
            customer=customer.id,
            items=[{
                'price': price_id,
            }],
            payment_behavior='default_incomplete',
            payment_settings={'save_default_payment_method': 'on_subscription'},
            expand=['latest_invoice.payment_intent'],
        )
        
        return Response({
            'subscription_id': subscription.id,
            'client_secret': subscription.latest_invoice.payment_intent.client_secret,
            'status': subscription.status,
            'customer_id': customer.id
        })
        
    except stripe.error.StripeError as e:
        return Response({'error': f'Stripe error: {str(e)}'}, status=400)
    except Exception as e:
        return Response({'error': f'Server error: {str(e)}'}, status=500)

@csrf_exempt
@api_view(['POST'])
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return JsonResponse({'error': 'Invalid payload'}, status=400)
    except stripe.error.SignatureVerificationError:
        return JsonResponse({'error': 'Invalid signature'}, status=400)
    
    # Handle subscription-specific events
    if event['type'] == 'invoice.payment_succeeded':
        invoice = event['data']['object']
        handle_successful_subscription_payment(invoice)
    elif event['type'] == 'invoice.payment_failed':
        invoice = event['data']['object']
        handle_failed_subscription_payment(invoice)
    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        handle_subscription_cancelled(subscription)
    elif event['type'] == 'customer.subscription.updated':
        subscription = event['data']['object']
        handle_subscription_updated(subscription)
    
    return JsonResponse({'status': 'success'})

def handle_successful_subscription_payment(invoice):
    """Handle successful subscription payment"""
    try:
        customer_id = invoice['customer']
        subscription_id = invoice['subscription']
        amount = invoice['amount_paid']
        
        # Get customer to find user_id
        customer = stripe.Customer.retrieve(customer_id)
        user_id = customer.metadata.get('user_id')
        
        if user_id:
            # Update user to premium status
            try:
                user = User.objects.get(id=user_id)  # Adjust to your User model
                user.account_tier = 'premium'
                user.save()
                print(f"User {user_id} upgraded to premium via subscription")
            except User.DoesNotExist:
                print(f"User {user_id} not found")
        
        print(f"Subscription payment succeeded: {subscription_id}, Amount: {amount}")
    except Exception as e:
        print(f"Error handling successful payment: {str(e)}")

def handle_failed_subscription_payment(invoice):
    """Handle failed subscription payment"""
    try:
        customer_id = invoice['customer']
        subscription_id = invoice['subscription']
        
        # Get customer to find user_id
        customer = stripe.Customer.retrieve(customer_id)
        user_id = customer.metadata.get('user_id')
        
        print(f"Subscription payment failed: {subscription_id}")
        # You might want to send an email notification here
        # Or give them a grace period before downgrading
        
    except Exception as e:
        print(f"Error handling failed payment: {str(e)}")

def handle_subscription_cancelled(subscription):
    """Handle subscription cancellation"""
    try:
        customer_id = subscription['customer']
        subscription_id = subscription['id']
        
        # Get customer to find user_id
        customer = stripe.Customer.retrieve(customer_id)
        user_id = customer.metadata.get('user_id')
        
        if user_id:
            # Downgrade user to free tier
            try:
                user = User.objects.get(id=user_id)  # Adjust to your User model
                user.account_tier = 'free'
                user.save()
                print(f"User {user_id} downgraded to free after subscription cancellation")
            except User.DoesNotExist:
                print(f"User {user_id} not found")
        
        print(f"Subscription cancelled: {subscription_id}")
    except Exception as e:
        print(f"Error handling subscription cancellation: {str(e)}")

def handle_subscription_updated(subscription):
    """Handle subscription updates (like plan changes)"""
    try:
        customer_id = subscription['customer']
        subscription_id = subscription['id']
        status = subscription['status']
        
        print(f"Subscription updated: {subscription_id}, Status: {status}")
        # Handle subscription status changes if needed
        
    except Exception as e:
        print(f"Error handling subscription update: {str(e)}")