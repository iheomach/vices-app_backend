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

# Complete Backend Views for Subscription Management
# Add these functions to your payments/views.py

# Make sure to import your custom User model:
# from your_app.models import User  # Replace 'your_app' with your actual app name
# Instead of: from django.contrib.auth.models import User

@api_view(['GET'])
def get_subscription_status(request, user_id):
    """Get subscription status and billing history for a user"""
    try:
        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=401)
        
        # Find user's customer in Stripe
        customers = stripe.Customer.list(
            metadata={'user_id': str(user_id)},
            limit=1
        )
        
        if not customers.data:
            return Response({
                'subscription': None,
                'invoices': [],
                'message': 'No subscription found'
            })
        
        customer = customers.data[0]
        
        # Get subscriptions
        subscriptions = stripe.Subscription.list(
            customer=customer.id,
            status='all',
            limit=1
        )
        
        subscription_data = None
        if subscriptions.data:
            sub = subscriptions.data[0]
            subscription_data = {
                'id': sub.id,
                'status': sub.status,
                'current_period_start': sub.current_period_start,
                'current_period_end': sub.current_period_end,
                'cancel_at_period_end': sub.cancel_at_period_end,
                'plan': {
                    'amount': sub.plan.amount if hasattr(sub, 'plan') else sub.items.data[0].price.unit_amount,
                    'currency': sub.plan.currency if hasattr(sub, 'plan') else sub.items.data[0].price.currency,
                    'interval': sub.plan.interval if hasattr(sub, 'plan') else sub.items.data[0].price.recurring.interval,
                }
            }
        
        # Get invoices
        invoices = stripe.Invoice.list(
            customer=customer.id,
            limit=10
        )
        
        invoice_data = []
        for invoice in invoices.data:
            invoice_data.append({
                'id': invoice.id,
                'amount_paid': invoice.amount_paid,
                'currency': invoice.currency,
                'status': invoice.status,
                'created': invoice.created,
                'hosted_invoice_url': invoice.hosted_invoice_url,
                'invoice_pdf': invoice.invoice_pdf,
            })
        
        return Response({
            'subscription': subscription_data,
            'invoices': invoice_data,
            'customer_id': customer.id
        })
        
    except stripe.error.StripeError as e:
        return Response({'error': f'Stripe error: {str(e)}'}, status=400)
    except Exception as e:
        return Response({'error': f'Server error: {str(e)}'}, status=500)

@api_view(['POST'])
def cancel_subscription(request):
    """Cancel a subscription"""
    try:
        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=401)
        
        data = request.data
        subscription_id = data.get('subscription_id')
        user_id = data.get('user_id')
        
        if not subscription_id:
            return Response({'error': 'Subscription ID required'}, status=400)
        
        # Cancel subscription at period end
        subscription = stripe.Subscription.modify(
            subscription_id,
            cancel_at_period_end=True
        )
        
        print(f"Subscription {subscription_id} marked for cancellation at period end")
        
        return Response({
            'message': 'Subscription will be cancelled at the end of the current period',
            'subscription_id': subscription.id,
            'cancel_at_period_end': subscription.cancel_at_period_end,
            'current_period_end': subscription.current_period_end
        })
        
    except stripe.error.StripeError as e:
        return Response({'error': f'Stripe error: {str(e)}'}, status=400)
    except Exception as e:
        return Response({'error': f'Server error: {str(e)}'}, status=500)

@api_view(['POST'])
def reactivate_subscription(request):
    """Reactivate a cancelled subscription"""
    try:
        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=401)
        
        data = request.data
        subscription_id = data.get('subscription_id')
        user_id = data.get('user_id')
        
        if not subscription_id:
            return Response({'error': 'Subscription ID required'}, status=400)
        
        # Reactivate subscription
        subscription = stripe.Subscription.modify(
            subscription_id,
            cancel_at_period_end=False
        )
        
        print(f"Subscription {subscription_id} reactivated")
        
        return Response({
            'message': 'Subscription reactivated successfully',
            'subscription_id': subscription.id,
            'cancel_at_period_end': subscription.cancel_at_period_end,
            'status': subscription.status
        })
        
    except stripe.error.StripeError as e:
        return Response({'error': f'Stripe error: {str(e)}'}, status=400)
    except Exception as e:
        return Response({'error': f'Server error: {str(e)}'}, status=500)

