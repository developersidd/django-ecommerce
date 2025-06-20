import string
import random
from django.conf import settings

from sslcommerz_lib import SSLCOMMERZ
from .models import PaymentGatewaySettings


def unique_transaction_id_generator(
    size=10, chars=string.ascii_uppercase + string.digits
):
    return "".join(random.choice(chars) for _ in range(size))



def sslcommerz_payment_gateway(request, name, amount, order_number):

    gateway_auth_details = PaymentGatewaySettings.objects.all().first()
    settings = {
        "store_id": gateway_auth_details.store_id,
        "store_pass": gateway_auth_details.store_pass,
        "issandbox": True,
    }

    sslcommez = SSLCOMMERZ(settings)
    post_body = {}
    post_body["total_amount"] = amount
    post_body["currency"] = "BDT"
    post_body["tran_id"] = unique_transaction_id_generator()
    post_body["success_url"] = f"http://127.0.0.1:8000/orders/payment_validate?order_number={order_number}"
    
    post_body["fail_url"] = "http://127.0.0.1:8000/orders/fail"
    post_body["cancel_url"] = "http://127.0.0.1:8000/cart"
    post_body["emi_option"] = 0
    post_body["cus_name"] = name
    post_body["cus_email"] = 'request.data["email"]'
    post_body["cus_phone"] = 'request.data["phone"]'
    post_body["cus_add1"] = 'request.data["address"]'
    post_body["cus_city"] = 'request.data["address"]'
    post_body["cus_country"] = "Bangladesh"
    post_body["shipping_method"] = "NO"
    post_body["multi_card_name"] = ""
    post_body["num_of_item"] = 1
    post_body["product_name"] = "Test"
    post_body["product_category"] = "Test Category"
    post_body["product_profile"] = "general"

    # OPTIONAL PARAMETERS
    post_body["value_a"] = name

    response = sslcommez.createSession(post_body)
    return (
        "https://sandbox.sslcommerz.com/gwprocess/v4/gw.php?Q=pay&SESSIONKEY="
        + response["sessionkey"]
    )
