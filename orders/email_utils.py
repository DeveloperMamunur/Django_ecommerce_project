from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags


def send_payment_success_email(order, request=None):
    subject = f'Payment Confirmation - Order #{order.order_number}'
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = order.customer.email
    
    if request:
        site_url = request.build_absolute_uri('/')[:-1]
    else:
        site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')

    context = {
        'customer_name': order.customer.get_full_name() or order.customer.username,
        'order_number': order.order_number,
        'order_date': order.created_at.strftime('%B %d, %Y'),
        'order_amount': order.order_amount,
        'shipping_charge': order.shipping_charge,
        'coupon_discount': order.coupon_discount,
        'vat_amount': order.vat_amount,
        'tax_amount': order.tax_amount,
        'grand_total': order.grand_total,
        'paid_amount': order.paid_amount,
        'order_details': order.order_details.all(),
        'shipping_address': order.shipping_address,
        'billing_address': order.billing_address,
        'site_url': site_url,
        'order_id': order.id,
    }

    html_content = render_to_string('emails/payment_success.html', context)
    text_content = strip_tags(html_content)
    
    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=from_email,
        to=[to_email]
    )
    email.attach_alternative(html_content, "text/html")
    
    try:
        email.send()
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False


def send_order_status_email(order, status):
    status_messages = {
        'processing': 'Your order is being processed',
        'shipped': 'Your order has been shipped',
        'delivered': 'Your order has been delivered',
        'cancelled': 'Your order has been cancelled',
    }
    
    subject = f'Order Update - {status_messages.get(status, "Order Status Changed")}'
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = order.customer.email
    
    context = {
        'customer_name': order.customer.get_full_name() or order.customer.username,
        'order_number': order.order_number,
        'status': status,
        'status_message': status_messages.get(status, 'Your order status has changed'),
        'order': order,
    }
    
    html_content = render_to_string('emails/order_status_update.html', context)
    text_content = strip_tags(html_content)
    
    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=from_email,
        to=[to_email]
    )
    email.attach_alternative(html_content, "text/html")
    
    try:
        email.send()
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False