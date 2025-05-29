from django.shortcuts import render, redirect
from .forms import RegisterForm
from .models import Account, UserProfile


# Verification email
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage


def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            cleaned_data = form.cleaned_data()
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
                    "token": default_token_generator.make_token(user),
                },
            )
            to_email = email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()
            # messages.success(request, 'Thank you for registering with us. We have sent you a verification email to your email address [rathan.kumar@gmail.com]. Please verify it.')
            return redirect(f"/accounts/login/?command=verification&email={email}")

    else:
        form = RegisterForm()
    context = {"form": form}
    return render(request, "accounts/register.html", context)


def login(request):
    return render(request, "accounts/login.html")


def logout(request):
    return
