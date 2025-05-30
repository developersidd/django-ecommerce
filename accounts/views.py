from django.shortcuts import render, redirect, get_object_or_404
from .forms import RegistrationForm
from .models import Account, UserProfile

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
def register(request):
    print(
        "🐍 File: accounts/views.py | Line: 27 | register ~ request.user",
        request.user.is_authenticated,
    )
    if request.user.is_authenticated:
        return redirect("home")
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
            #messages.success(
            #    request,
            #    f"Thank you for registering with us. We have sent you a verification email to your email address [{email}]. Please verify it.",
            #)
            return redirect(f"/accounts/login/?command=verification&email={email}")

    else:
        form = RegistrationForm()
    context = {"form": form}
    return render(request, "accounts/register.html", context)


# Login User
def login(request):
     if request.user.is_authenticated:
        return redirect("home")
    if request.method == "POST":
        email = request.POST["email"]
        password = request.POST["password"]

        user = auth.authenticate(request, email=email, password=password)
        print("🐍 File: accounts/views.py | Line: 96 | login ~ user", user)
        auth.login(request, user)
        return redirect("home")
        if user != None:
            try:
                cart = Cart.objects.get(cart_id=_cart_id(request))
            except:
                pass
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


# Dashboard
def dashboard(request):
    pass
