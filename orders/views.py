from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from products.models import Product
from .models import Cart, CartItem

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