from django.shortcuts import render
from store.models import Product


def home(request):
    products = Product.objects.filter(is_available=True).order_by("created_date")
    return render(request, "home.html", {"products": products})
