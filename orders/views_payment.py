from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.shortcuts import redirect
from django.contrib import messages
from django.core import signing
from django.db.models import Sum, F
from django.utils import timezone
from django.conf import settings
from uuid import uuid4
import requests
from django.contrib.auth.decorators import login_required


from .models import Order, OnlinePaymentRequest, OrderPayment, Coupon


@login_required
@csrf_exempt
def start_payment(request):
    if request.method == "POST":
        order_id = request.POST.get("order_id")

        if not order_id:
            return JsonResponse({"success": False, "message": "Order ID missing"})

        response_data, status = create_payment_request(request, order_id)

        return JsonResponse(response_data, status=status)

    return JsonResponse({"success": False, "message": "Invalid request"})

@csrf_exempt
def payment_create(request):
    response_data = {}
    error_message = []

    try:
        if request.method == 'POST':
            post_dict = {key: value for key, value in request.POST.items()}

            order_id = post_dict.get("ecom_order_id", None)
            payment_method = post_dict.get("payment_method", '')

            if not order_id:
                error_message.append("Please provide order id")
            if not payment_method:
                error_message.append("Please provide payment_method")

            if all([order_id, payment_method]):
                create_payment_request(request, order_id)

            response_data.update({
                'success': False,
                "error_message": error_message
            })
        else:
            response_data.update({
                'success': False,
                "error_message": f"{request.method} not allowed"
            })
    except Exception as e:
        response_data.update({
            'success': False,
            "error_message": f"Error: {e}"
        })
    return JsonResponse(response_data, status=400)


def create_payment_request(request, order_id):
    transaction_id = str(uuid4())
    order_obj = Order.objects.filter(id=order_id).last()

    user = order_obj.customer

    success_url = request.build_absolute_uri(f'/payment/success/{transaction_id}/')
    fail_url = request.build_absolute_uri(f'/payment/fail/{transaction_id}/')
    cancel_url = request.build_absolute_uri(f'/payment/cancel/{transaction_id}/')

    OnlinePaymentRequest.objects.create(
        order=order_obj,
        transaction_id=transaction_id,
        amount=order_obj.grand_total,
        payment_status='Pending',
        created_by=request.user,
    )

    payment_data = {
        'store_id': settings.SSLCOMMERZ_STORE_ID,
        'store_passwd': settings.SSLCOMMERZ_STORE_PASSWORD,
        'total_amount': order_obj.grand_total,
        'currency': 'BDT',
        'tran_id': transaction_id,
        'success_url': success_url,
        'fail_url': fail_url,
        'cancel_url': cancel_url,
        'cus_name': user.get_full_name() or user.username,
        'cus_email': user.email,
        'cus_phone': user.profile.phone,
        'cus_add1': order_obj.billing_address.address if order_obj.billing_address else '',
        'cus_city': 'Dhaka',
        'cus_country': 'Bangladesh',
        'shipping_method': 'NO',
        'product_name': 'Order Payment',
        'product_category': 'Ecommerce',
        'product_profile': 'general',
    }

    print(f"Payment Data: {payment_data}")

    response = requests.post(settings.SSLCOMMERZ_API_URL, data=payment_data)
    data = response.json()

    if data.get('status') == 'SUCCESS':
        response_data = {
            'GatewayPageURL': data['GatewayPageURL'],
            'status': 'SUCCESS',
        }
        response_status = 200
    else:
        response_data = {
            'status': 'FAILED',
            'message': data.get('failedreason', 'Unknown error occurred')
        }
        response_status = 400

    return response_data, response_status


@csrf_exempt
def payment_complete(request, str_data):
    
    val_id = request.POST.get('val_id')

    try:
        payment_object = OnlinePaymentRequest.objects.get(transaction_id=str_data)
    except OnlinePaymentRequest.DoesNotExist:
        messages.error(request, "Invalid transaction")
        return redirect('home')
    
    if payment_object.payment_status != 'Paid':
        status_data = verify_ssl_payment(val_id)

        if status_data:
            update_payment_in_order(payment_object.transaction_id)
            messages.success(request, f"Payment confirmed for order {payment_object.order.id}")

        else:
            messages.error(request, "Payment verification failed")
            return redirect('home')
    else:
        messages.success(request, "Your requested payment has already been paid")

    return redirect('home')


def verify_ssl_payment(val_id):
    payload = {
        'val_id': val_id,
        'store_id': settings.SSLCOMMERZ_STORE_ID,
        'store_passwd': settings.SSLCOMMERZ_STORE_PASSWORD,
        'v': '1',
        'format': 'json'
    }

    response = requests.get(settings.SSLCOMMERZ_VALIDATION_API, params=payload)
    print(f"SSL Verification Response: {response.text}")
    result = response.json()
    
    if result.get('status') == 'VALID':
        return True
    return False


@csrf_exempt
def payment_check(request, str_data):
    pk = signing.loads(str_data)
    payment_object = OnlinePaymentRequest.objects.get(id=pk)

    if payment_object.transaction_id:
        status = verify_ssl_payment(payment_object.transaction_id)
        return JsonResponse({'status': status})

    return JsonResponse({'status': False})


@csrf_exempt
def payment_cancel(request, str_data):
    payment_object = OnlinePaymentRequest.objects.get(transaction_id=str_data)

    if payment_object.payment_status != "Paid":
        payment_object.payment_status = "Cancelled"
        payment_object.save()

    return redirect('home')


@csrf_exempt
def payment_failed(request, str_data):
    payment_object = OnlinePaymentRequest.objects.get(transaction_id=str_data)

    if payment_object.payment_status != "Paid":
        payment_object.payment_status = "Failed"
        payment_object.save()

    return redirect('home')


@transaction.atomic
def update_payment_in_order(transaction_id):
    payment_object = OnlinePaymentRequest.objects.select_for_update().filter(
        transaction_id=transaction_id
    ).first()

    if not payment_object:
        return False

    order = payment_object.order  # ✅ ASSIGN EARLY

    # Prevent double processing
    if payment_object.payment_status == "Paid":
        return True

    # Mark payment as paid
    payment_object.payment_status = "Paid"
    payment_object.updated_at = timezone.now()
    payment_object.save(update_fields=["payment_status", "updated_at"])

    # Create order payment record
    OrderPayment.objects.create(
        order=order,
        payment_method="SSL",
        amount=payment_object.amount,
        transaction_id=transaction_id
    )

    # Recalculate total paid
    total_paid = OrderPayment.objects.filter(
        order=order,
        is_active=True
    ).aggregate(
        total_paid=Sum('amount')
    )['total_paid'] or Decimal('0.00')

    order.paid_amount = total_paid
    order.due_amount = order.grand_total - total_paid

    # Coupon usage update (SAFE)
    if order.coupon_discount > 0 and hasattr(order, 'applied_coupon') and order.applied_coupon:
        Coupon.objects.filter(
            id=order.applied_coupon.id
        ).update(used_count=F('used_count') + 1)

    if order.due_amount <= 0:
        order.paid_status = 'paid'
        order.status = 'processing'

    order.save(update_fields=[
        'paid_amount',
        'due_amount',
        'paid_status',
        'status'
    ])

    return True