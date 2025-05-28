from .views import _cart_id
from carts.models import Cart, CartItem


def counter(request):
    if "admin" in request.path:
        print("🐍 File: carts/context_processors.py | Line: 7 | counter", True)

        return {}

    else:
        cart_count = 0
        try:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart)
            cart_count = len(cart_items)
        except cart.DoesNotExist:
            print("🐍 File: carts/context_processors.py | Line: 17 | counter ~ e", e)
            cart_count = 0
        return dict(cart_count=cart_count)
