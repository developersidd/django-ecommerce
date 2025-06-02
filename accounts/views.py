from django.shortcuts import render, redirect, get_object_or_404
from .forms import RegistrationForm
from .models import Account, UserProfile
from .decorators import unauthenticated_user

# from orders.models import Order, OrderProduct
from django.contrib import messages, auth
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

# Verification email
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage

from carts.views import _cart_id
from carts.models import Cart, CartItem

# import requests


# Register User
@unauthenticated_user
def register(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            first_name = cleaned_data["first_name"]
            last_name = cleaned_data["last_name"]
            email = cleaned_data["email"]
            username = email.split("@")[0]
            phone_number = cleaned_data["phone_number"]
            password = cleaned_data["password"]
            user = Account.objects.create_user(
                first_name=first_name,
                last_name=last_name,
                email=email,
                username=username,
                password=password,
            )
            user.phone_number = phone_number
            user.save()

            # Create a User profile
            profile = UserProfile()
            profile.user = user
            profile.profile_picture = "default/default-user.png"
            profile.save()

            # Send email for account activation
            current_site = get_current_site(request)
            mail_subject = "Please active you account"
            message = render_to_string(
                "accounts/account_verification_email.html",
                {
                    "user": user,
                    "domain": current_site,
                    "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                    "token": default_token_generator.make_token(
                        user
                    ),  # the token is one time use
                },
            )
            to_email = email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()
            return redirect(f"/accounts/login/?command=verification&email={email}")

    else:
        form = RegistrationForm()
    context = {"form": form}
    return render(request, "accounts/register.html", context)


# Login User
@unauthenticated_user
def login(request):
    if request.method == "POST":
        email = request.POST["email"]
        password = request.POST["password"]

        user = auth.authenticate(request, email=email, password=password)
        if user != None:
            try:
                cart = Cart.objects.get(cart_id=_cart_id(request))
                is_cart_items_exists = CartItem.objects.filter(cart=cart).exists()
                if is_cart_items_exists:
                    # Getting the products which were added before sign in
                    cart_items = CartItem.objects.filter(cart=cart)
                    # variations of before logged In cart items
                    product_variation_ids = []
                    for item in cart_items:
                        product_variation_ids = sorted(
                            list(item.variations.values_list("id", flat=True))
                        )
                        # get variations of old user cart items
                        ex_cart_items = CartItem.objects.filter(user=user)
                        for ex_item in ex_cart_items:
                            ex_variation_ids = sorted(
                                list(ex_item.variations.values_list("id", flat=True))
                            )
                            # if old product variation exist in the new cart items then increase the quantity
                            if product_variation_ids == ex_variation_ids:
                                item.quantity += ex_item.quantity
                                item.user = user
                                item.save()
                                ex_item.delete()
                            else:
                                item.user = user
                                #ex_item = user
                                #ex_item.save()
                                item.save()
                auth.login(request, user)
            except Exception as e:
                pass
            auth.login(request, user)
            messages.success(request, "You are logged in.")
            return redirect("dashboard")

    return render(request, "accounts/login.html")


# Active account
def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None

    if user != None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, "Congratulations! YOur account is activated")
        return redirect("login")
    else:
        messages.error(request, "Invalid activation link!")
        return redirect("register")


# Logout
@login_required(login_url="login")
def logout(request):
    auth.logout(request)
    messages.success(request, "You are logged out")
    return redirect("login")


# Forgot Password
@unauthenticated_user
def forgotPassword(request):
    if request.method == "POST":
        email = request.POST["email"]
        print("🐍 File: accounts/views.py | Line: 131 | forgotPassword ~ email", email)

        if Account.objects.filter(email=email).exists():
            user = Account.objects.get(email__exact=email)
            # Send email for reset password
            current_site = get_current_site(request)
            mail_subject = "Please Reset your password"
            message = render_to_string(
                "accounts/reset_password_email.html",
                {
                    "user": user,
                    "domain": current_site,
                    "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                    "token": default_token_generator.make_token(user),
                },
            )
            to_email = email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()
            messages.success(
                request, "Password reset email has been send to you email address"
            )
            return redirect("login")
        else:

            print(
                "🐍 File: accounts/views.py | Line: 158 | forgotPassword ~ error",
                "NOT EXIST",
            )
            messages.error(request, "Account doesn't exist!")
            return redirect("forgotPassword")

    return render(request, "accounts/forgotPassword.html")


# Reset password
@unauthenticated_user
def resetpassword_validate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None
        token = ""
    if user != None and default_token_generator.check_token(user, token):
        request.session["uid"] = uid
        messages.success(request, "Please reset you password")
        return redirect("resetPassword")
    else:
        messages.error(request, "This link has been expired!")
        return redirect("login")


# Reset password
@unauthenticated_user
def resetPassword(request):
    if request.method == "POST":
        password = request.POST["password"]
        confirm_password = request.POST["confirm_password"]
        if password != confirm_password:
            messages.error(request, "Password and confirm password does not matched!")
            return redirect("resetPassword")
        else:
            uid = request.session["uid"]
            user = Account._default_manager.get(pk=uid)
            user.set_password(password)
            user.save()
            messages.success(request, "Password reset successful")
            return redirect("login")
    else:
        return render(request, "accounts/resetPassword.html")


# Dashboard
@login_required(login_url="login")
def dashboard(request):
    return render(request, "accounts/dashboard.html")


# My Orders
@login_required(login_url="login")
def my_orders(request):
    return render(request, "accounts/my_orders.html")


# My edit Profile
@login_required(login_url="login")
def edit_profile(request):
    return render(request, "accounts/edit_profile.html")


# Change Password
@login_required(login_url="login")
def change_password(request):
    return render(request, "accounts/change_password.html")
