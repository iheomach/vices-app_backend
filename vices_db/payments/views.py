import stripe
import json
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth import get_user_model

User = get_user_model()

stripe.api_key = settings.STRIPE_SECRET_KEY
@api_view(['POST'])
def create_subscription(request):
    try:
        data = request.data
        price_id = data.get('price_id')
        user_id = data.get('user_id')
        email = data.get('email')
        payment_method_id = data.get('payment_method_id')

        if not price_id or not email or not payment_method_id:
            return Response({'error': 'Missing required fields'}, status=400)

        # Create or get customer
        customers = stripe.Customer.list(email=email, limit=1)
        if customers.data:
            customer = customers.data[0]
        else:
            customer_data = {'email': email}
            if user_id:
                customer_data['metadata'] = {'user_id': str(user_id)}
            customer = stripe.Customer.create(**customer_data)

        # Attach payment method
        try:
            stripe.PaymentMethod.attach(payment_method_id, customer=customer.id)
        except stripe.error.InvalidRequestError:
            pass  # Already attached

        # Set as default payment method
        stripe.Customer.modify(
            customer.id,
            invoice_settings={'default_payment_method': payment_method_id},
        )

        # Create subscription - let Stripe handle payment automatically
        subscription = stripe.Subscription.create(
            customer=customer.id,
            items=[{'price': price_id}],
            default_payment_method=payment_method_id,
            # No payment_behavior specified - Stripe will charge immediately if possible
        )

        print(f"✅ Subscription created: {subscription.id} with status: {subscription.status}")

        # For immediate charging, we don't need client_secret
        # Stripe will either charge successfully or fail with an error
        return Response({
            'subscription_id': subscription.id,
            'client_secret': None,  # Not needed for immediate charging
            'status': subscription.status,
            'customer_id': customer.id,
            'message': 'Subscription created successfully'
        })
            
    except stripe.error.StripeError as e:
        print(f"❌ Stripe error: {e}")
        return Response({'error': f'Stripe error: {str(e)}'}, status=400)
    except Exception as e:
        print(f"❌ Server error: {e}")
        return Response({'error': f'Server error: {str(e)}'}, status=500)

@api_view(['GET'])
def get_subscription_status(request, user_id):
    """Get subscription status and billing history for a user"""
    try:
        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=401)
        
        print(f"🔍 Looking for customer with user_id: {user_id} (type: {type(user_id)})")
        
        # Search for customer correctly
        customers = stripe.Customer.list(limit=100)
        
        # Find customer manually to avoid metadata search issues
        customer = None
        for cust in customers.data:
            if cust.metadata.get('user_id') == str(user_id):
                customer = cust
                break
        
        if not customer:
            print(f"🔍 No customer found for user_id: {user_id}")
            return Response({
                'subscription': None,
                'invoices': [],
                'message': 'No subscription found'
            })
        
        print(f"🔍 Found customer: {customer.id}")
        
        # Get subscriptions
        subscriptions = stripe.Subscription.list(
            customer=customer.id,
            status='all',
            limit=1
        )
        
        subscription_data = None
        if subscriptions.data:
            sub = subscriptions.data[0]
            
            # Get the first subscription item (there's usually only one)
            subscription_item = sub.items.data[0] if sub.items.data else None
            
            # ✅ FIXED: Access current_period_start/end from subscription object, not subscription_item
            subscription_data = {
                'id': sub.id,
                'object': sub.object,
                'status': sub.status,
                'current_period_start': sub.current_period_start,  # ✅ From subscription object
                'current_period_end': sub.current_period_end,      # ✅ From subscription object
                'cancel_at_period_end': sub.cancel_at_period_end,
                'created': sub.created,
                'customer': sub.customer,
                # Include items structure for frontend compatibility
                'items': {
                    'object': 'list',
                    'data': [{
                        'id': subscription_item.id,
                        'object': 'subscription_item',
                        'price': {
                            'id': subscription_item.price.id,
                            'object': 'price',
                            'active': subscription_item.price.active,
                            'unit_amount': subscription_item.price.unit_amount,
                            'currency': subscription_item.price.currency,
                            'recurring': {
                                'interval': subscription_item.price.recurring.interval,
                                'interval_count': subscription_item.price.recurring.interval_count,
                            }
                        },
                        'quantity': subscription_item.quantity,
                    }]
                } if subscription_item else {'object': 'list', 'data': []},
                # Legacy plan object for backward compatibility
                'plan': {
                    'amount': subscription_item.price.unit_amount if subscription_item else None,
                    'currency': subscription_item.price.currency if subscription_item else 'usd',
                    'interval': subscription_item.price.recurring.interval if subscription_item else 'month',
                } if subscription_item else None
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
        
        if not subscription_id:
            return Response({'error': 'Subscription ID required'}, status=400)
        
        subscription = stripe.Subscription.modify(
            subscription_id,
            cancel_at_period_end=True
        )
        
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
        
        if not subscription_id:
            return Response({'error': 'Subscription ID required'}, status=400)
        
        subscription = stripe.Subscription.modify(
            subscription_id,
            cancel_at_period_end=False
        )
        
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

# Webhook handler and helper functions
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
    
    if event['type'] == 'invoice.payment_succeeded':
        handle_successful_subscription_payment(event['data']['object'])
    elif event['type'] == 'invoice.payment_failed':
        handle_failed_subscription_payment(event['data']['object'])
    elif event['type'] == 'customer.subscription.deleted':
        handle_subscription_cancelled(event['data']['object'])
    elif event['type'] == 'customer.subscription.updated':
        handle_subscription_updated(event['data']['object'])
    
    return JsonResponse({'status': 'success'})

def handle_successful_subscription_payment(invoice):
    try:
        customer = stripe.Customer.retrieve(invoice['customer'])
        user_id = customer.metadata.get('user_id')
        
        if user_id:
            user = User.objects.get(id=user_id)
            user.account_tier = 'premium'
            user.save()
            print(f"User {user_id} upgraded to premium via subscription")
    except Exception as e:
        print(f"Error handling successful payment: {str(e)}")

def handle_failed_subscription_payment(invoice):
    try:
        print(f"Subscription payment failed: {invoice['subscription']}")
    except Exception as e:
        print(f"Error handling failed payment: {str(e)}")

def handle_subscription_cancelled(subscription):
    try:
        customer = stripe.Customer.retrieve(subscription['customer'])
        user_id = customer.metadata.get('user_id')
        
        if user_id:
            user = User.objects.get(id=user_id)
            user.account_tier = 'free'
            user.save()
            print(f"User {user_id} downgraded to free")
    except Exception as e:
        print(f"Error handling cancellation: {str(e)}")

def handle_subscription_updated(subscription):
    try:
        print(f"Subscription updated: {subscription['id']}, Status: {subscription['status']}")
    except Exception as e:
        print(f"Error handling update: {str(e)}")
