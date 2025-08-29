from django.contrib import admin
from .models import Customer, CustomerContact

class CustomerContactInline(admin.TabularInline):  # so you can add multiple contacts under one customer
    model = CustomerContact
    extra = 1


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("designation", "company_name", "location", "email")
    inlines = [CustomerContactInline]


@admin.register(CustomerContact)
class CustomerContactAdmin(admin.ModelAdmin):
    list_display = ("contact_name", "contact_detail", "customer")
