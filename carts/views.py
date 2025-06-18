from django.shortcuts import render, redirect
from store.models import Product
from .models import Cart, CartItem
from django.core.exceptions import ObjectDoesNotExist
from carts.models import Variation
import math
import logging
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required

logger = logging.getLogger(__name__)


def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()

    return cart


# Create your views here.
def cart(request, total=0, quantity=0, cart_items=None):
    tax = 0
    grand_total = 0
    try:
        current_user = request.user

        if current_user.is_authenticated:
            cart_items = CartItem.objects.filter(user=current_user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
            total += cart_item.product.price * cart_item.quantity
            quantity += cart_item.quantity
        tax = math.ceil((2 * total) / 100)
        grand_total = total + tax
    except ObjectDoesNotExist:
        pass

    context = {
        "cart_items": cart_items,
        "total": total,
        "quantity": quantity,
        "tax": tax,
        "grand_total": grand_total,
    }
    return render(request, "store/cart.html", context)


# Add to cart
def add_cart(request, product_id):
    product = Product.objects.get(id=product_id)
    product_variations = []
    if request.method == "POST":
        for item in request.POST:
            key = item
            value = request.POST[key]
            try:
                variation = Variation.objects.get(
                    product=product,
                    variation_category__iexact=key,
                    variation_value__iexact=value,
                )
                product_variations.append(variation)

            except:
                pass
    try:
        cart = Cart.objects.get(
            cart_id=_cart_id(request)
        )  # get the cart_id from session

    except Cart.DoesNotExist:
        cart = Cart.objects.create(cart_id=_cart_id(request))
        cart.save()
    try:
        current_user = request.user

        if current_user.is_authenticated:
            is_cart_item_exists = CartItem.objects.filter(
                product=product, user=current_user
            ).exists()
        else:
            is_cart_item_exists = CartItem.objects.filter(
                product=product, cart=cart
            ).exists()
        print(
            "🐍 File: carts/views.py | Line: 83 | add_cart ~ is_cart_item_exists",
            is_cart_item_exists,
        )
        if is_cart_item_exists:
            if current_user.is_authenticated:
                cart_items = CartItem.objects.filter(product=product, user=current_user)
            else:
                cart_items = CartItem.objects.filter(product=product, cart=cart)

            print(
                "🐍 File: carts/views.py | Line: 98 | add_cart ~ cart_items", cart_items
            )
            # Loop thought the all item to check is the same variant product
            item_variation_ids = []
            ids = []
            for item in cart_items:
                variation = list(item.variations.values_list("id", flat=True))
                item_variation_ids.append(sorted(variation))
                ids.append(item.id)
            id_list = list(v.id for v in product_variations)
            product_variation_ids = sorted(id_list)

            # Match the variations id
            if product_variation_ids in item_variation_ids:
                index = item_variation_ids.index(product_variation_ids)
                item_id = ids[index]
                item = cart_items
                item = CartItem.objects.get(product=product, id=item_id)
                item.quantity += 1
                item.save()
                return redirect("cart")
            # if not match that means new variation then add the product into cart
            else:
                user = None
                if current_user.is_authenticated:
                    user = current_user
                item = CartItem.objects.create(
                    product=product, quantity=1, cart=cart, user=user
                )
                print("Creating product")
                if len(product_variations) > 0:
                    item.variations.clear()
                    item.variations.add(*product_variations)
                item.save()

        else:
            # if the product doesn't exist then add the product
            user = None
            if current_user.is_authenticated:
                user = current_user
            cart_item = CartItem.objects.create(
                cart=cart, product=product, quantity=1, user=user
            )

            # Add variations to cart item
            if len(product_variations) > 0:
                cart_item.variations.set(product_variations)
            cart_item.save()
        return redirect("cart")
    except Exception as e:
        print("🐍 File: carts/views.py | Line: 97 | add_cart ~ e", e)
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


# Checkout
@login_required(login_url="login")
def checkout(request, total=0, quantity=0, cart_items=None):
    try:
        tax = 0
        grand_total = 0
        current_user = request.user
        cart_items = CartItem.objects.filter(user=current_user, is_active=True)
        for cart_item in cart_items:
            total += cart_item.product.price * cart_item.quantity
            quantity += cart_item.quantity
        tax = math.ceil((2 * total) / 100)
        grand_total = total + tax
    except ObjectDoesNotExist:
        pass

    context = {
        "cart_items": cart_items,
        "total": total,
        "quantity": quantity,
        "tax": tax,
        "grand_total": grand_total,
    }
    return render(request, "store/checkout.html", context)
