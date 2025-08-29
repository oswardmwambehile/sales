from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import CustomUser, NewVisit
from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.utils.safestring import mark_safe
import csv
from django.http import HttpResponse


# --- Custom User Creation Form ---
class CustomUserCreationForm(forms.ModelForm):
    """A form for creating new users."""
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)

    class Meta:
        model = CustomUser
        fields = ('email', 'first_name', 'last_name', 'position', 'zone', 'branch', 'contact')

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


# --- Custom User Change Form ---
class CustomUserChangeForm(forms.ModelForm):
    """A form for updating users."""
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = CustomUser
        fields = (
            'email', 'password', 'first_name', 'last_name',
            'position', 'zone', 'branch', 'contact',
            'is_active', 'is_staff', 'is_superuser'
        )

    def clean_password(self):
        return self.initial["password"]


# --- Custom Admin ---
class CustomUserAdmin(BaseUserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    list_display = (
        'email', 'first_name', 'last_name', 'position',
        'zone', 'branch', 'contact', 'is_staff', 'is_superuser'
    )
    list_filter = ('is_staff', 'is_superuser', 'position', 'zone', 'branch')
    search_fields = ('email', 'first_name', 'last_name', 'contact')
    ordering = ('email',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'contact')}),
        ('Job Info', {'fields': ('position', 'zone', 'branch')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 'first_name', 'last_name', 'position', 'zone', 'branch', 'contact',
                'password1', 'password2', 'is_active', 'is_staff', 'is_superuser'
            )}
        ),
    )


# --- Register the custom user model with admin ---
admin.site.register(CustomUser, CustomUserAdmin)


# --- NewVisit Admin ---
@admin.register(NewVisit)
class NewVisitAdmin(admin.ModelAdmin):
    # Columns in list view
    list_display = (
        "id", "client_name_or_company", "contact_person", "contact_number",
        "designation", "productionline", "meeting_purpose",
        "meeting_outcome", "is_order_quoted", "order_amount",
        "added_by", "created_at"
    )
    list_display_links = ("id", "client_name_or_company")

    # Filters on the right
    list_filter = ("productionline", "designation", "is_order_quoted", "created_at")

    # Search bar
    search_fields = (
        "company_name__company_name",       # ✅ related Customer
        "contact_person__contact_name",     # ✅ related Contact
        "contact_number", "meeting_purpose",
        "meeting_outcome", "item_discussed"
    )

    # Fields you cannot edit
    readonly_fields = ("created_at", "updated_at", "added_by", "location_preview")

    # Form layout
    fieldsets = (
        ("Client Information", {
            "fields": ("company_name", "contact_person", "contact_number", "designation")
        }),
        ("Production Line", {
            "fields": ("productionline",)
        }),
        ("Meeting Details", {
            "fields": ("meeting_purpose", "meeting_outcome", "item_discussed")
        }),
        ("Order Details", {
            "fields": ("is_order_quoted", "order_amount", "reason_no_order")
        }),
        ("Location", {
            "fields": ("latitude", "longitude", "location_preview"),
        }),
        ("Tracking", {
            "fields": ("added_by", "created_at", "updated_at"),
        }),
    )

    # Save user automatically
    def save_model(self, request, obj, form, change):
        if not obj.added_by:
            obj.added_by = request.user
        super().save_model(request, obj, form, change)

    # Show Google Maps preview inside admin
    def location_preview(self, obj):
        if obj.latitude and obj.longitude:
            return mark_safe(
                f'<a href="https://www.google.com/maps?q={obj.latitude},{obj.longitude}" target="_blank">'
                f"View on Map ({obj.latitude}, {obj.longitude})</a>"
            )
        return "No location set"
    location_preview.short_description = "Map Location"

    # ✅ Custom method for list_display
    def client_name_or_company(self, obj):
        return obj.company_name.company_name if obj.company_name else "—"
    client_name_or_company.short_description = "Company / Client"

    # Custom admin action: Export selected to CSV
    actions = ["export_as_csv"]

    def export_as_csv(self, request, queryset):
        meta = self.model._meta
        field_names = [field.name for field in meta.fields]

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename={meta.model_name}.csv'
        writer = csv.writer(response)

        writer.writerow(field_names)
        for obj in queryset:
            writer.writerow([getattr(obj, field) for field in field_names])
        return response

    export_as_csv.short_description = "Export Selected to CSV"
