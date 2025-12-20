from django.db import transaction
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

def delete_coupon(request, coupon_id):
    coupon = get_object_or_404(Coupon, id=coupon_id)
    coupon.delete()
    return redirect('coupon_list')

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


def add_to_cart(request):
    if request.method == "POST":
        product_id = request.POST.get("product_id")
        product = get_object_or_404(Product, id=product_id)
        cart = get_user_cart(request)

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={
                "quantity": 1,
                "price": float(product.sale_price if product.on_sale else product.price)
            }
        )
        if not created:
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
    cart_items = cart.cart_items.all()
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
def checkout(request):
    cart = request.session.get('cart', {})
    total = sum(float(i['price']) * i['quantity'] for i in cart.values())

    return render(request, 'frontend/checkout.html', {
        'cart_total': total
    })


@require_POST
def apply_coupon(request):
    code = request.POST.get('code')

    try:
        coupon = Coupon.objects.get(code=code)
        now = timezone.now()

        if not (coupon.valid_from <= now <= coupon.valid_to):
            return JsonResponse({'success': False, 'message': 'Coupon expired'})

        if coupon.used_count >= coupon.usage_limit:
            return JsonResponse({'success': False, 'message': 'Coupon limit reached'})

        cart = request.session.get('cart', {})
        subtotal = sum(
            Decimal(str(i['price'])) * i['quantity']
            for i in cart.values()
        )

        if coupon.discount_type == 'percent':
            discount = (subtotal * coupon.discount_value) / Decimal('100')
        else:
            discount = coupon.discount_value

        discount = min(discount, subtotal)

        request.session['coupon'] = coupon.id

        return JsonResponse({
            'success': True,
            'discount': float(discount)  # JSON needs float
        })

    except Coupon.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Invalid coupon'})


@require_POST
@login_required
@transaction.atomic
def place_order(request):
    cart = request.session.get('cart', {})
    if not cart:
        return JsonResponse({'success': False, 'message': 'Cart is empty'})

    # Shipping
    shipping = ShippingAddress.objects.create(
        full_name=request.POST.get('full_name'),
        email=request.POST.get('email'),
        phone=request.POST.get('phone'),
        address=request.POST.get('address'),
        city=request.POST.get('city'),
        state=request.POST.get('state'),
        country=request.POST.get('country', 'Bangladesh'),
        zip_code=request.POST.get('zip'),
    )

    subtotal = sum(
        Decimal(str(item['price'])) * item['quantity']
        for item in cart.values()
    )

    shipping_charge = Decimal('50')
    discount = Decimal('0')
    coupon = None

    coupon_id = request.session.get('coupon')
    if coupon_id:
        coupon = Coupon.objects.select_for_update().get(id=coupon_id)

        if coupon.discount_type == 'percent':
            discount = (subtotal * coupon.discount_value) / Decimal('100')
        else:
            discount = coupon.discount_value

        discount = min(discount, subtotal)

    grand_total = subtotal - discount + shipping_charge

    order = Order.objects.create(
        customer=request.user,
        shipping_address=shipping,
        order_amount=subtotal,
        shipping_charge=shipping_charge,
        coupon_discount=discount,
        grand_total=grand_total,
        paid_amount=Decimal('0'),
        due_amount=grand_total,
        payment_method='COD',
        payment_status='PENDING',
    )

    for item in cart.values():
        OrderDetail.objects.create(
            order=order,
            product_id=item['product_id'],
            unit_price=Decimal(str(item['price'])),
            quantity=item['quantity'],
            total_price=Decimal(str(item['price'])) * item['quantity']
        )

    # COD → mark as unpaid but confirmed
    if coupon:
        coupon.used_count += 1
        coupon.save()
        request.session.pop('coupon', None)

    request.session['cart'] = {}

    return JsonResponse({
        'success': True,
        'order_id': order.id
    })