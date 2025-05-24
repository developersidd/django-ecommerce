from django.shortcuts import render, get_object_or_404
from .models import Product
from category.models import Category
from django.db.models import Q


# Create your views here.
def store(request, category_slug=None):
    categories = None
    search_by = request.GET.get("search") or ""
    products = None
    if category_slug != None:
        categories = get_object_or_404(Category, slug=category_slug)
        products = Product.objects.filter(category=categories, is_available=True)
        product_count = products.count()
    elif search_by != None:
        products = Product.objects.filter(Q(product_name__icontains=search_by))
        product_count = products.count()
    else:
        products = Product.objects.filter(is_available=True)
        product_count = products.count()

    context = {"products": products, "product_count": product_count}
    return render(request, "store/store.html", context)


# product details
def product_detail(request, category_slug, product_slug):
    try:
        product = Product.objects.get(category__slug=category_slug, slug=product_slug)
        context = {"single_product": product}
        return render(request, "store/product_detail.html", context)
    except Exception as e:
        raise e
