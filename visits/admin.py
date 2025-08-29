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




from django.contrib import admin
from .models import DailyFollowUp, FollowUp, FollowUpSubmission


# 🔹 Inline FollowUps under DailyFollowUp
class FollowUpInline(admin.TabularInline):  # or StackedInline for more spacing
    model = FollowUp
    extra = 0
    fields = (
        'productionline',
        'company_name',
        'contact_person',
        'meeting_purpose',
        'meeting_outcome',
        'is_order_quoted',
        'order_amount',
        'is_payment_collected',
        'payment_amount',
    )
    readonly_fields = ('created_at', 'updated_at')


# 🔹 Admin for DailyFollowUp
@admin.register(DailyFollowUp)
class DailyFollowUpAdmin(admin.ModelAdmin):
    list_display = ('serial_number', 'user', 'date', 'created_at')
    list_filter = ('date', 'user')
    search_fields = ('serial_number', 'user__email')
    inlines = [FollowUpInline]
    ordering = ('-date',)


# 🔹 Admin for FollowUp
@admin.register(FollowUp)
class FollowUpAdmin(admin.ModelAdmin):
    list_display = (
        'company_name', 'contact_person', 'productionline',
        'is_order_quoted', 'order_amount',
        'is_payment_collected', 'payment_amount',
        'created_at',
    )
    list_filter = (
        'productionline', 'is_order_quoted', 'is_payment_collected', 'created_at'
    )
    search_fields = ('company_name__company_name', 'contact_person__contact_name')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Basic Info', {
            'fields': ('daily_followup', 'productionline', 'company_name', 'contact_person')
        }),
        ('Contact Snapshot', {
            'fields': ('contact_number', 'designation', 'latitude', 'longitude')
        }),
        ('Meeting Details', {
            'fields': ('meeting_purpose', 'meeting_outcome', 'item_discussed')
        }),
        ('Order Info', {
            'fields': ('is_order_quoted', 'order_amount', 'reason_no_order')
        }),
        ('Payment Info', {
            'fields': ('is_payment_collected', 'payment_amount', 'reason_no_payment')
        }),
        ('Meta', {
            'fields': ('added_by', 'created_at', 'updated_at')
        }),
    )


# 🔹 Admin for FollowUpSubmission
@admin.register(FollowUpSubmission)
class FollowUpSubmissionAdmin(admin.ModelAdmin):
    list_display = ('daily_followup', 'user', 'final_status')
    list_filter = ('final_status',)
    search_fields = ('user__email', 'daily_followup__serial_number')


from django.contrib import admin
from .models import DailyVisitForm, NewVisit, FormSubmission


@admin.register(DailyVisitForm)
class DailyVisitFormAdmin(admin.ModelAdmin):
    list_display = ('serial_number', 'user', 'date', 'created_at')
    list_filter = ('date',)
    search_fields = ('user__email', 'serial_number')


@admin.register(NewVisit)
class NewVisitAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'contact_person', 'productionline', 'is_order_quoted', 'order_amount', 'created_at')
    list_filter = ('productionline', 'is_order_quoted', 'created_at')
    search_fields = ('company_name__company_name', 'contact_person__contact_name', 'meeting_purpose', 'meeting_outcome')


@admin.register(FormSubmission)
class FormSubmissionAdmin(admin.ModelAdmin):
    list_display = ('user', 'daily_form', 'final_status', 'created_at')
    list_filter = ('final_status', 'created_at')
    search_fields = ('user__email',)


