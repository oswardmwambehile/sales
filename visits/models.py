from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator
from django.conf import settings
from django.utils.timezone import now, localdate


# -------------------
# Custom User
# -------------------
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email must be provided")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    POSITION_CHOICES = [
        ('Head of Sales', 'Head of Sales'),
        ('Facilitator', 'Facilitator'),
        ('Product Brand Manager', 'Product Brand Manager'),
        ('Corporate Manager', 'Corporate Manager'),
        ('Corporate Officer', 'Corporate Officer'),
        ('Zonal Sales Executive', 'Zonal Sales Executive'),
        ('Mobile Sales Officer', 'Mobile Sales Officer'),
        ('Desk Sales Officer', 'Desk Sales Officer'),
        ('Admin', 'Admin'),
    ]

    ZONE_CHOICES = [
        ('Coast Zone', 'Coast Zone'),
        ('Corporate', 'Corporate'),
        ('Central Zone', 'Central Zone'),
        ('Southern Zone', 'Southern Zone'),
        ('Northern Zone', 'Northern Zone'),
        ('Lake Zone', 'Lake Zone'),
    ]

    BRANCH_CHOICES = [
        ('Chanika', 'Chanika'),
        ('Mikocheni', 'Mikocheni'),
        ('Morogoro', 'Morogoro'),
        ('Zanzibar', 'Zanzibar'),
        ('ANDO HQ', 'ANDO HQ'),
        ('Dodoma', 'Dodoma'),
        ('Singida', 'Singida'),
        ('Tabora', 'Tabora'),
        ('Mbeya', 'Mbeya'),
        ('Tunduma', 'Tunduma'),
        ('Arusha', 'Arusha'),
        ('Moshi', 'Moshi'),
        ('Mwanza', 'Mwanza'),
        ('Geita', 'Geita'),
    ]

    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=50, null=True, blank=True)
    last_name = models.CharField(max_length=50, null=True, blank=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    position = models.CharField(max_length=100, choices=POSITION_CHOICES, null=True, blank=True)
    zone = models.CharField(max_length=100, choices=ZONE_CHOICES, null=True, blank=True)
    branch = models.CharField(max_length=100, choices=BRANCH_CHOICES, null=True, blank=True)

    contact = models.CharField(
        max_length=13,
        null=True,
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^(?:\+255|0)[67][0-9]\d{7}$',
                message="Enter a valid Tanzanian phone number (e.g. +255712345678 or 0712345678)"
            )
        ]
    )

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self):
        return self.first_name


# -------------------
# Daily Visit Form (UNIQUE - keep only this one)
# -------------------
from django.db import models
from django.conf import settings
from django.utils.timezone import localdate   # ✅ for default date
from customer.models import *
# -------------------
# Daily Visit Form
# -------------------
class DailyVisitForm(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="daily_forms",
        null=True,
        blank=True,
    )
    date = models.DateField(default=localdate)
    serial_number = models.PositiveIntegerField(unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'date')   # 👈 only one per user per day

    def save(self, *args, **kwargs):
        if not self.pk:
            today = self.date
            count_today = DailyVisitForm.objects.filter(date=today).count() + 1
            self.serial_number = int(today.strftime("%Y%m%d")) * 1000 + count_today
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Daily Form {self.serial_number} - {self.user.email} - {self.date}"


# -------------------
# New Visit
# -------------------
class NewVisit(models.Model):
    
    PRODUCTION_LINE_CHOICES = [
        ("RESIN_ROOFING_SHEETS", "RESIN ROOFING SHEETS"),
        ("ROOF_PAINT", "ROOF PAINT"),
        ("UPVC", "UPVC"),
        ("WALL_COATING", "WALL COATING"),
        ("ZEBRA_TILES", "ZEBRA TILES"),
    ]

    daily_form = models.ForeignKey(
        "DailyVisitForm",
        on_delete=models.CASCADE,
        related_name="visits",
        null=True,
        blank=True,
    )

    company_name = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="visits", null=True, blank=True)
    contact_person = models.ForeignKey(CustomerContact, on_delete=models.CASCADE, related_name="visits" ,null=True, blank=True)

    # Auto-filled snapshot from contact at time of visit
    contact_number = models.CharField(max_length=255, blank=True, null=True)
    designation = models.CharField(max_length=255,  blank=True, null=True)

    productionline = models.CharField(max_length=30, choices=PRODUCTION_LINE_CHOICES, null=True, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    meeting_purpose = models.CharField(max_length=255)
    meeting_outcome = models.CharField(max_length=255)
    item_discussed = models.TextField(max_length=255)

    # Order logic
    is_order_quoted = models.BooleanField(default=False)
    order_amount = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    reason_no_order = models.TextField(null=True, blank=True)

    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
            company = self.company_name.company_name if self.company_name else "No Company"
            contact = self.contact_person.contact_name if self.contact_person else "No Contact"
            return f"Visit: {company} - {contact}"
# -------------------
# Form Submission Workflow
# -------------------
class FormSubmission(models.Model):
    STATUS_CHOICES = [
        ('opened', 'Opened'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('resubmite', 'Resubmite'),
    ]



    # Link to the daily form being reviewed
    daily_form = models.OneToOneField(
        DailyVisitForm,
        on_delete=models.CASCADE,
        related_name="submission"
    )

    # The owner who submitted visits
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='submissions'
    )

    final_status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='opened')
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True,)




from django.db import models
from django.utils.timezone import localdate, now
from .models import CustomUser  # ✅ your custom user model


# -------------------
# Daily Follow Up (same as DailyVisitForm)
# -------------------
class DailyFollowUp(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="daily_followups"
    )
    date = models.DateField(default=localdate)
    serial_number = models.PositiveIntegerField(unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'date')

    def save(self, *args, **kwargs):
        if not self.pk:
            today = self.date
            count_today = DailyFollowUp.objects.filter(date=today).count() + 1
            self.serial_number = int(today.strftime("%Y%m%d")) * 1000 + count_today
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Daily FollowUp {self.serial_number} - {self.user.email} - {self.date}"


# -------------------
# Follow Up (same as NewVisit + payment fields)
# -------------------
class FollowUp(models.Model):
    PRODUCTION_LINE_CHOICES = [
        ('RESIN_ROOFING_SHEETS', 'RESIN ROOFING SHEETS'),
        ('ROOF_PAINT', 'ROOF PAINT'),
        ('UPVC', 'UPVC'),
        ('WALL_COATING', 'WALL COATING'),
        ('ZEBRA_TILES', 'ZEBRA TILES'),
    ]

    daily_followup = models.ForeignKey(
        DailyFollowUp,
        on_delete=models.CASCADE,
        related_name="followups",
        null=True,
        blank=True
    )

    productionline = models.CharField(
        max_length=30,
        choices=PRODUCTION_LINE_CHOICES,
        null=True,
        blank=True,
    )

    company_name = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="followups",   # ✅ no clash with NewVisit
        null=True,
        blank=True
    )

    contact_person = models.ForeignKey(
        CustomerContact,
        on_delete=models.CASCADE,
        related_name="followup_contacts",  # ✅ no clash with NewVisit
        null=True,
        blank=True
    )

    # Auto-filled snapshot from contact at time of visit
    contact_number = models.CharField(max_length=255, blank=True, null=True)
    designation = models.CharField(max_length=255, blank=True, null=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    meeting_purpose = models.CharField(max_length=255)
    meeting_outcome = models.CharField(max_length=255)
    item_discussed = models.TextField(max_length=255)

    # Order quoted logic
    is_order_quoted = models.BooleanField(default=False)
    order_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    reason_no_order = models.TextField(null=True, blank=True)

    # Payment collection logic
    is_payment_collected = models.BooleanField(default=False)
    payment_amount = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    reason_no_payment = models.TextField(null=True, blank=True)

    added_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"FollowUp - {self.company_name} - {self.designation}"


# -------------------
# Follow Up Submission (same as FormSubmission)
# -------------------
class FollowUpSubmission(models.Model):
    STATUS_CHOICES = [
        ('opened', 'Opened'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('resubmite', 'Resubmite'),
    ]



    daily_followup = models.OneToOneField(
        DailyFollowUp,
        on_delete=models.CASCADE,
        related_name="submission"
    )

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='followup_submissions'
    )

    final_status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='opened')



