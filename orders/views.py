from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.urls import reverse
from carts.models import CartItem
from django.shortcuts import redirect
from .forms import OrderForm
from .models import Order, OrderProduct, Payment
from store.models import Product
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.http import HttpResponse, JsonResponse
import datetime
import json
from urllib.parse import urlencode
from .sslcommerz import sslcommerz_payment_gateway
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt, csrf_protect


# Place Order
@login_required(login_url="login")
def place_order(request, total=0, quantity=0):
    current_user = request.user

    # if no item in cart then redirect to store page
    cart_items = CartItem.objects.filter(user=current_user)
    cart_count = cart_items.count()
    grand_total = 0
    tax = 0
    if cart_count <= 0:
        redirect("store")

    for item in cart_items:
        total += item.product.price * item.quantity
        quantity += item.quantity

    tax = (2 * grand_total) / 100
    grand_total = total + tax
    if request.method == "POST":
        form = OrderForm(request.POST)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            data = Order()
            data.user = current_user
            data.first_name = cleaned_data["first_name"]
            data.last_name = cleaned_data["last_name"]
            data.phone = cleaned_data["phone"]
            data.email = cleaned_data["email"]
            data.address_line_1 = cleaned_data["address_line_1"]
            data.address_line_2 = cleaned_data["address_line_2"]
            data.country = cleaned_data["country"]
            data.state = cleaned_data["state"]
            data.city = cleaned_data["city"]
            data.order_note = cleaned_data["order_note"]
            data.order_total = grand_total
            data.tax = tax
            data.ip = request.META.get("REMOTE_ADDR")
            data.save()

            # Generate order number
            yr = int(datetime.date.today().strftime("%Y"))
            dt = int(datetime.date.today().strftime("%d"))
            mt = int(datetime.date.today().strftime("%m"))
            d = datetime.date(yr, mt, dt)
            current_date = d.strftime("%Y%m%d")  # 20210305
            order_number = current_date + str(data.id)
            data.order_number = order_number
            data.save()

            print(" order:", data)
            order = Order.objects.get(
                user=current_user, is_ordered=False, order_number=order_number
            )

            context = {
                "order": order,
                "cart_items": cart_items,
                "tax": tax,
                "total": total,
                "grand_total": grand_total,
            }

        return render(request, "orders/payments.html", context)
    else:
        return redirect("checkout")


def ssl_payment(request):
    order_number = request.POST["order_number"]
    name = request.POST["full_name"]
    amount = request.POST["total_amount"]

    return redirect(sslcommerz_payment_gateway(request, name, amount, order_number))


@csrf_exempt
def payment_validate(request):
    if request.method == "POST":
        body = request.POST
        status = body.get("status")
        if status == "VALID" or status == "SUCCESS":
            order_number = request.GET["order_number"]
            payment_method = body["card_type"]
            tran_id = body["tran_id"]
            base_url = reverse("payment_success")
            query_string = urlencode(
                {
                    "order_number": order_number,
                    "tran_id": tran_id,
                    "payment_method": payment_method,
                    "status": status,
                }
            )
            url = f"{base_url}?{query_string}"
            return redirect(url)


@login_required(login_url="login")
def payment_success(request):
    tran_id = request.GET["tran_id"]
    payment_method = request.GET["payment_method"]
    status = request.GET["status"]
    order_number = request.GET["order_number"]
    if request.method == "GET" and request.user.is_authenticated:
        order = Order.objects.get(
            user=request.user, is_ordered=False, order_number=order_number
        )

        # Store transaction details inside Payment model
        payment = Payment(
            user=request.user,
            payment_id=tran_id,
            payment_method=payment_method,
            amount_paid=order.order_total,
            status=status,
        )
        payment.save()

        order.payment = payment
        order.is_ordered = True
        order.save()

        # Move the cart items to Order Product table
        cart_items = CartItem.objects.filter(user=request.user)

        for item in cart_items:
            orderproduct = OrderProduct()
            orderproduct.order_id = order.id
            orderproduct.payment = payment
            orderproduct.user_id = request.user.id
            orderproduct.product_id = item.product_id
            orderproduct.quantity = item.quantity
            orderproduct.product_price = item.product.price
            orderproduct.ordered = True
            orderproduct.save()

            cart_item = CartItem.objects.get(id=item.id)
            product_variation = cart_item.variations.all()
            orderproduct = OrderProduct.objects.get(id=orderproduct.id)
            orderproduct.variations.set(product_variation)
            orderproduct.save()

            # Reduce the quantity of the sold products
            product = Product.objects.get(id=item.product_id)
            product.stock -= item.quantity
            product.save()

        # Clear cart
        CartItem.objects.filter(user=request.user).delete()

        # Send order received email to customer
        mail_subject = "Thank you for your order!"
        message = render_to_string(
            "orders/order_received_email.html",
            {
                "user": request.user,
                "order": order,
            },
        )
        to_email = request.user.email
        send_email = EmailMessage(mail_subject, message, to=[to_email])
        send_email.send()
        base_url = reverse("order_complete")
        query_string = urlencode(
            {"order_number": order_number, "payment_id": payment.payment_id}
        )
        url = f"{base_url}?{query_string}"
        return redirect(url)
    return redirect("cart")


# order complete
def order_complete(request):
    order_number = request.GET.get("order_number")
    trans_id = request.GET.get("payment_id")

    try:
        order = Order.objects.get(order_number=order_number, is_ordered=True, user=request.user)
        ordered_products = OrderProduct.objects.filter(order_id=order.id)

        subtotal = 0
        for i in ordered_products:
            subtotal += i.product_price * i.quantity

        payment = Payment.objects.get(payment_id=trans_id)

        context = {
            "order": order,
            "ordered_products": ordered_products,
            "order_number": order.order_number,
            "transID": payment.payment_id,
            "payment": payment,
            "subtotal": subtotal,
        }
        return render(request, "orders/order_complete.html", context)
    except (Payment.DoesNotExist, Order.DoesNotExist):
        return redirect("home")
