from django.db import transaction, IntegrityError
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from products.models import Product
from .models import Cart, CartItem, Coupon, ShippingAddress, Order, OrderDetail
from django.utils import timezone
from decimal import Decimal



@login_required
def coupon_list(request):
    coupons = Coupon.objects.all()
    if request.method == 'POST':
        coupon_id = request.POST.get('coupon_id')
        code = request.POST.get('code')
        discount_type = request.POST.get('discount_type')
        discount_value = request.POST.get('discount_value')
        valid_from = request.POST.get('valid_from')
        valid_to = request.POST.get('valid_to')
        usage_limit = request.POST.get('usage_limit')
        used_count = request.POST.get('used_count')

        if coupon_id:
            coupon = get_object_or_404(Coupon, id=coupon_id)
            coupon.code = code
            coupon.discount_type = discount_type
            coupon.discount_value = discount_value
            coupon.valid_from = valid_from
            coupon.valid_to = valid_to
            coupon.usage_limit = usage_limit
            coupon.used_count = used_count
            coupon.save()
        else:
            coupon = Coupon.objects.create(
                code=code,
                discount_type=discount_type,
                discount_value=discount_value,
                valid_from=valid_from,
                valid_to=valid_to,
                usage_limit=usage_limit,
                used_count=used_count
            )
            coupon.save()
    return render(request, 'coupons/coupon_list.html', {'coupons': coupons})

@login_required
def delete_coupon(request, coupon_id):
    coupon = get_object_or_404(Coupon, id=coupon_id)
    coupon.delete()
    return redirect('coupon_list')

@login_required
def toggle_coupon_status(request, coupon_id):
    coupon = get_object_or_404(Coupon, id=coupon_id)
    coupon.is_active = not coupon.is_active
    coupon.save()
    return redirect('coupon_list')


def get_user_cart(request):
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
    else:
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        cart, _ = Cart.objects.get_or_create(session_key=session_key, user=None)
    return cart

def get_cart_items(cart):
    return cart.cart_items.filter(is_active=True)

def add_to_cart(request):
    if request.method == "POST":
        product_id = request.POST.get("product_id")
        product = get_object_or_404(Product, id=product_id)
        cart = get_user_cart(request)
        order = Order.objects.filter(customer=request.user, status='pending', is_active=True).first()

        with transaction.atomic():
            try:
                cart_item, created = CartItem.all_objects.update_or_create(
                    cart=cart,
                    product=product,
                    defaults={
                        'is_active': True,
                        'price': float(product.sale_price if product.on_sale else product.price),
                        'quantity': 1
                    }
                )
                if not created:
                    cart_item.quantity += 1
                    cart_item.save()
            except IntegrityError:
                cart_item = CartItem.objects.get(cart=cart, product=product)
                cart_item.quantity += 1
                cart_item.save()

        return JsonResponse({"success": True, "cart": serialize_cart(cart)})

    return JsonResponse({"success": False}, status=400)


def remove_from_cart(request):
    if request.method == "POST":
        product_id = request.POST.get("product_id")
        cart = get_user_cart(request)

        try:
            cart_item = CartItem.objects.get(cart=cart, product_id=product_id)
            cart_item.delete()
        except CartItem.DoesNotExist:
            pass

        return JsonResponse({"success": True, "cart": serialize_cart(cart)})

    return JsonResponse({"success": False}, status=400)


def get_cart(request):
    cart = get_user_cart(request)
    return JsonResponse({"cart": serialize_cart(cart)})


def serialize_cart(cart):
    cart_items = cart.cart_items.filter(is_active=True)

    return [
        {
            "product_id": item.product.id,
            "name": item.product.name,
            "quantity": item.quantity,
            "price": float(item.price),
            "image": item.product.get_primary_image(),
        }
        for item in cart_items
    ]


@require_POST
def update_cart_quantity(request):
    product_id = request.POST.get("product_id")
    quantity = int(request.POST.get("quantity", 1))

    cart = get_user_cart(request)

    try:
        cart_item = CartItem.objects.get(cart=cart, product_id=product_id)
        cart_item.quantity = quantity
        cart_item.save()
    except CartItem.DoesNotExist:
        return JsonResponse({"success": False, "error": "Cart item not found"})

    return JsonResponse({"success": True})

@login_required
@transaction.atomic
def checkout(request):
    cart = get_user_cart(request)
    cart_items = cart.cart_items.filter(is_active=True)

    if not cart_items.exists():
        return redirect('cart')

    order_amount = sum(
        Decimal(item.price) * item.quantity
        for item in cart_items
    )

    coupon_discount = Decimal('0.00')
    applied_coupon = None
    coupon_id = request.session.get('coupon')

    if coupon_id:
        try:
            coupon = Coupon.objects.get(
                id=coupon_id,
                is_active=True,
                valid_from__lte=timezone.now(),
                valid_to__gte=timezone.now()
            )
            applied_coupon = coupon

            if coupon.discount_type == 'percent':
                coupon_discount = (order_amount * coupon.discount_value) / 100
            else:
                coupon_discount = Decimal(coupon.discount_value)

            coupon_discount = min(coupon_discount, order_amount)

        except Coupon.DoesNotExist:
            request.session.pop('coupon', None)


    vat_amount = Decimal('0.00') 
    tax_amount = Decimal('0.00')
    shipping_charge = Decimal('50.00')

    grand_total = (
        order_amount
        + vat_amount
        + tax_amount
        + shipping_charge
        - coupon_discount
    )

    order, created = Order.objects.get_or_create(
        customer=request.user,
        status='pending',
        defaults={
            'order_amount': order_amount,
            'coupon_discount': coupon_discount,
            'vat_amount': vat_amount,
            'tax_amount': tax_amount,
            'shipping_charge': shipping_charge,
            'grand_total': grand_total,
            'paid_amount': Decimal('0.00'),
            'due_amount': grand_total
        }
    )

    if not created:
        order.order_amount = order_amount
        order.coupon_discount = coupon_discount
        order.vat_amount = vat_amount
        order.tax_amount = tax_amount
        order.shipping_charge = shipping_charge
        order.grand_total = grand_total
        order.due_amount = grand_total - order.paid_amount
        order.save()

    order.order_details.all().delete()

    for item in cart_items:
        OrderDetail.objects.create(
            order=order,
            product=item.product,
            unit_price=item.price,
            quantity=item.quantity,
            total_price=item.price * item.quantity
        )

    if request.method == 'POST':
        return redirect('payment')

    return render(request, 'frontend/checkout.html', {
        'order': order,
        'cart_items': cart_items,
        'cart_total': order_amount,
        'order_amount': order_amount,
        'coupon_discount': coupon_discount,
        'vat_amount': vat_amount,
        'tax_amount': tax_amount,
        'shipping_charge': shipping_charge,
        'grand_total': grand_total,
        'applied_coupon': applied_coupon,
})

def apply_coupon(request):
    code = request.POST.get('code')

    try:
        coupon = Coupon.objects.get(code=code, is_active=True)
        now = timezone.now()

        if not (coupon.valid_from <= now <= coupon.valid_to):
            return JsonResponse({'success': False, 'message': 'Coupon expired'})

        if coupon.used_count >= coupon.usage_limit:
            return JsonResponse({'success': False, 'message': 'Coupon limit reached'})

        cart = get_user_cart(request)
        cart_items = get_cart_items(cart)

        if not cart_items.exists():
            return JsonResponse({'success': False, 'message': 'Cart is empty'})

        subtotal = sum(Decimal(item.price) * item.quantity for item in cart_items)

        if coupon.discount_type == 'percent':
            discount = subtotal * coupon.discount_value / Decimal('100')
        else:
            discount = coupon.discount_value

        discount = min(discount, subtotal)

        order = Order.objects.filter(customer=request.user, status='pending', is_active=True).first()
        if order:
            order.coupon_discount = discount
            order.grand_total = order.order_amount + order.shipping_charge - discount
            order.save(update_fields=['coupon_discount', 'grand_total'])

        request.session['coupon'] = coupon.id

        return JsonResponse({
            'success': True,
            'discount': float(discount),
            'grand_total': float(order.grand_total) if order else float(subtotal - discount)
        })

    except Coupon.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Invalid coupon'})


def remove_coupon(request):
    request.session['coupon'] = None
    Order.objects.filter(customer=request.user, status='pending', is_active=True).update(coupon_discount=0)
    return JsonResponse({'success': True})


@login_required
def place_order(request):
    if request.method == "POST":
        order = Order.objects.filter(customer=request.user, status='pending', is_active=True).first()
        if not order:
            return JsonResponse({"success": False, "message": "Order not found"})

        # Save shipping address
        shipping = ShippingAddress.objects.create(
            full_name=request.POST['full_name'],
            email=request.POST['email'],
            phone=request.POST['phone'],
            address=request.POST['address'],
            city=request.POST['city'],
            state=request.POST['state'],
            country=request.POST['country'],
            zip_code=request.POST['zip']
        )

        order.shipping_address = shipping
        order.status = 'processing'
        order.paid_amount = order.grand_total
        order.due_amount = 0
        order.save(update_fields=['shipping_address', 'status', 'paid_amount', 'due_amount'])

        # Deactivate cart items (soft-delete)
        CartItem.objects.filter(cart=get_user_cart(request), is_active=True).update(is_active=False)

        return JsonResponse({
            "success": True,
            "order_id": order.id
        })