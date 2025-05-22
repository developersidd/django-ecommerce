from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Account


# Register your models here.
class AccountAdmin(UserAdmin):
    list_display = (
        "email",
        "first_name",
        "last_name",
        "username",
        "last_login",
        "is_active",
        "date_joined",
    )

    list_display_links = ("email", "first_name", "last_name")

    # telling django that we are not using those missing fields in AbstractBaseUser since we are using it
    filter_horizontal = ()
    list_filter = ()
    fieldsets = ()
    # when you extend UserAdmin then it makes the password readonly for security reasons
    readonly_fields = ("email", "last_login", "date_joined")
    ordering = ("-date_joined",)


admin.site.register(Account, AccountAdmin)
