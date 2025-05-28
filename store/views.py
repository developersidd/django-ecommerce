from django.shortcuts import render, get_object_or_404
from .models import Product
from category.models import Category
from carts.models import CartItem
from carts.views import _cart_id
from django.db.models import Q
from django.core.paginator import PageNotAnInteger, Paginator, EmptyPage


# Create your views here.
def store(request, category_slug=None):
    categories = None
    # page = None
    # paged_products = None
    search_by = request.GET.get("search") or None
    # products = None
    if category_slug != None:
        categories = get_object_or_404(Category, slug=category_slug)
        products = Product.objects.filter(
            category=categories, is_available=True
        ).order_by("id")
        product_count = products.count()
    elif search_by != None:
        products = Product.objects.filter(
            Q(product_name__icontains=search_by)
        ).order_by("id")
        product_count = products.count()
    else:
        products = Product.objects.filter(is_available=True).order_by("id")
        product_count = products.count()

    paginator = Paginator(
        products,
        6,
    )
    page = request.GET.get("page")
    paged_products = paginator.get_page(page)

    context = {
        "products": paged_products,
        "product_count": product_count,
    }
    return render(request, "store/store.html", context)


# product details
def product_detail(request, category_slug, product_slug):
    try:
        product = Product.objects.get(category__slug=category_slug, slug=product_slug)
        in_cart = CartItem.objects.filter(
            cart__cart_id=_cart_id(request), product=product
        ).exists()

        context = {"single_product": product}
        return render(request, "store/product_detail.html", context)
    except Exception as e:
        raise e
