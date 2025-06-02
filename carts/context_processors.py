from .views import _cart_id
from carts.models import Cart, CartItem
from django.core.exceptions import ObjectDoesNotExist


def counter(request):
    if "admin" in request.path:
        return {}

    else:
        cart_count = 0
        cart = None
        try:
            current_user = request.user
            if current_user.is_authenticated:
                cart_items = CartItem.objects.filter(user=current_user)
            else:
                cart = Cart.objects.get(cart_id=_cart_id(request))
                cart_items = CartItem.objects.filter(cart=cart)
            cart_count = len(cart_items)
        except ObjectDoesNotExist:
            cart_count = 0
        return dict(cart_count=cart_count)
