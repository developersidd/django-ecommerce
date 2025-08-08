from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, ReviewRating, ProductGallery
from django.urls import reverse
from category.models import Category
from carts.models import CartItem
from carts.views import _cart_id
from django.db.models import Q
from django.core.paginator import PageNotAnInteger, Paginator, EmptyPage
from .forms import ReviewForm
from django.contrib import messages
from orders.models import OrderProduct


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
    # print("🐍 File: store/views.py | Line: 53 |  ~ product_slug", product_slug)
    # print(
    #    "🐍 File: store/views.py | Line: 53 |  ~ category_slug", category_slug
    # )
    try:
        single_product = Product.objects.get(
            category__slug=category_slug, slug=product_slug
        )

        in_cart = CartItem.objects.filter(
            cart__cart_id=_cart_id(request), product=single_product
        ).exists()
    except Exception as e:
        raise e

    if request.user.is_authenticated:
        try:
            orderproduct = OrderProduct.objects.filter(
                user=request.user, product_id=single_product.id
            ).exists()
        except OrderProduct.DoesNotExist:
            orderproduct = None
    else:
        orderproduct = None

    # Get the reviews
    reviews = ReviewRating.objects.filter(product_id=single_product.id, status=True)

    # Get the product gallery
    product_gallery = ProductGallery.objects.filter(product=single_product)

    context = {
        "single_product": single_product,
        "in_cart": in_cart,
        "product_gallery": product_gallery,
        "orderproduct": orderproduct,
        "reviews": reviews,
        #'product_gallery': product_gallery,
    }
    return render(request, "store/product_detail.html", context)


# Submit Review
def submit_review(request, product_id):
    current_user = request.user
    url = request.META.get("HTTP_REFERER")
    # Get the product to ensure it exists
    try:
        product = Product.objects.get(id=product_id)
        print("🐍 File: store/views.py | Line: 98 | submit_review ~ product", product)
    except Product.DoesNotExist:
        messages.error(request, "Product not found.")
        return redirect("store")
    # product = Product.objects.get(id=product_id)
    if request.method == "POST":
        print("🐍 File: store/views.py | Line: 65 | undefined ~ product_id", product_id)
        print("🐍 File: store/views.py | Line: 66 | submit_review ~ url", url)
        try:
            review = ReviewRating.objects.get(
                user__id=current_user.id, product__id=product_id
            )
            form = ReviewForm(request.POST, instance=review)
            form.save()
            messages.success(request, "Thank you! Your review has been updated.")
            # return redirect(
            #    reverse("product_detail", args=[product.category.slug, product.slug])
            # )
            return redirect(url)

        except ReviewRating.DoesNotExist:
            form = ReviewForm(request.POST)
            if form.is_valid():
                data = ReviewRating()
                cleaned_data = form.cleaned_data
                data.subject = cleaned_data["subject"]
                data.rating = cleaned_data["rating"]
                data.review = cleaned_data["review"]
                data.ip = request.META.get("REMOTE_ADDR")
                data.product_id = product_id
                data.user_id = current_user.id
                data.save()
                messages.success(request, "Thank you! Your review has been submitted.")

                # return redirect(
                #    reverse(
                #        "product_detail", args=[product.category.slug, product.slug]
                #    )
                # )
                return redirect(url)
