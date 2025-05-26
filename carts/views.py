from django.shortcuts import render, redirect
from store.models import Product
from .models import Cart, CartItem
import math
import logging
from django.shortcuts import get_object_or_404

logger = logging.getLogger(__name__)


def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()

    return cart


# Create your views here.
def cart(request, total=0, quantity=0, cart_items=None):
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
            total += cart_item.product.price * cart_item.quantity
            quantity += cart_item.quantity
        tax = math.ceil((2 * total) / 100)
        grand_total = total + tax
    except cart.DoesNotExist:
        pass

    context = {
        "cart_items": cart_items,
        "total": total,
        "quantity": quantity,
        "tax": tax,
        "grand_total": grand_total,
    }
    return render(request, "store/cart.html", context)


def add_cart(request, product_id):
    product = Product.objects.get(id=product_id)
    try:
        cart = Cart.objects.get(
            cart_id=_cart_id(request)
        )  # get the cart_id from session

    except Cart.DoesNotExist:
        cart = Cart.objects.create(cart_id=_cart_id(request))
        cart.save()
    try:
        cartItem = CartItem.objects.get(product=product, cart=cart)
        cartItem.quantity += 1
        cartItem.save()
        return redirect("cart")
    except CartItem.DoesNotExist:
        cartItem = CartItem.objects.create(cart=cart, product=product, quantity=1)
        cartItem.save()
        return redirect("cart")


# Decrease cart item quantity
def remove_cart(request, product_id, cart_item_id):
    try:
        product = get_object_or_404(Product, id=product_id)
        cart_item = get_object_or_404(CartItem, id=cart_item_id, product=product)
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
        return redirect("cart")

    except Exception as e:
        logging.error(f"There was an error occurred")
        return None


# Remove Cart Item
def remove_cart_item(request, product_id, cart_item_id):
    try:
        product = get_object_or_404(Product, id=product_id)
        cart_item = CartItem.objects.get(pk=cart_item_id, product=product)
        cart_item.delete()
        return redirect("cart")

    except Exception as e:
        logging.error(
            f"There was an error occurred while deleting cart item with Id: {cart_item_id}"
        )
        return None
