
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render

from django.shortcuts import get_object_or_404

from django.shortcuts import render, get_object_or_404, redirect
from django.shortcuts import render, get_object_or_404, redirect
# Create your views here.
def index(request):
    return render(request, 'manager/index.html')


def add_visit(request):
    return render(request, 'manager/add_vist.html')

def select_visit(request):
    return render(request, 'manager/select_visit.html')

# visits/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.timezone import localdate
from django.http import JsonResponse
from .forms import NewVisitForm
from .models import DailyVisitForm, FormSubmission, CustomerContact


# -------------------------------
# Helper: Get or create daily form
# -------------------------------
def get_or_create_daily_form(user, date=None):
    if date is None:
        date = localdate()

    daily_form, created = DailyVisitForm.objects.get_or_create(
        user=user,
        date=date
    )

    # 🔑 Ensure a FormSubmission is created for tracking status
    if created and not hasattr(daily_form, "submission"):
        FormSubmission.objects.create(daily_form=daily_form, user=user)

    return daily_form


# -------------------------------
# Create a new visit
# -------------------------------
@login_required
def new_visit(request):
    if request.method == "POST":
        form = NewVisitForm(request.POST)
        if form.is_valid():
            visit = form.save(commit=False)
            visit.added_by = request.user

            # 🔗 Always attach today's DailyVisitForm
            visit.daily_form = get_or_create_daily_form(request.user)

            # ✅ Auto-fill contact number + designation from selected contact
            if visit.contact_person:
                try:
                    contact = CustomerContact.objects.get(id=visit.contact_person.id)
                    visit.contact_number = contact.contact_detail          # phone
                    visit.designation = contact.customer.designation       # designation from Customer
                except CustomerContact.DoesNotExist:
                    pass

            visit.save()
            print(">>> VISIT SAVED:", visit.id, visit.company_name, visit.contact_person)  # debug
            return redirect("select_vist")  # success redirect
        else:
            # ❌ FORM INVALID
            print(">>> FORM ERRORS:", form.errors)  # debug
    else:
        form = NewVisitForm()

    return render(request, "manager/new_visit.html", {"form": form})


# -------------------------------
# AJAX: Get contacts for a company
# -------------------------------
@login_required
def get_contacts(request, company_id):
    contacts = CustomerContact.objects.filter(customer_id=company_id)
    data = [
        {
            "id": c.id,
            "name": c.contact_name,
        }
        for c in contacts
    ]
    return JsonResponse({"contacts": data})


# -------------------------------
# AJAX: Get details for a contact
# -------------------------------
@login_required
def get_contact_details(request, contact_id):
    contact = get_object_or_404(CustomerContact, id=contact_id)
    data = {
        "contact_number": contact.contact_detail,           # from CustomerContact
        "designation": contact.customer.designation,        # from related Customer
    }
    return JsonResponse(data)



# visits/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.timezone import localdate
from django.http import JsonResponse
from .forms import FollowUpForm   # ✅ you must create a form like NewVisitForm
from .models import (
    DailyFollowUp,
    FollowUp,
    FollowUpSubmission,
    CustomerContact,
)


# -------------------------------
# Helper: Get or create daily followup form
# -------------------------------
def get_or_create_daily_followup(user, date=None):
    if date is None:
        date = localdate()

    daily_followup, created = DailyFollowUp.objects.get_or_create(
        user=user,
        date=date
    )

    # 🔑 Ensure a FollowUpSubmission is created for tracking status
    if created and not hasattr(daily_followup, "submission"):
        FollowUpSubmission.objects.create(daily_followup=daily_followup, user=user)

    return daily_followup


# -------------------------------
# Create a new followup
# -------------------------------
@login_required
def new_followup(request):
    if request.method == "POST":
        form = FollowUpForm(request.POST)
        if form.is_valid():
            followup = form.save(commit=False)
            followup.added_by = request.user

            # 🔗 Always attach today's DailyFollowUp
            followup.daily_followup = get_or_create_daily_followup(request.user)

            # ✅ Auto-fill contact number + designation from selected contact
            if followup.contact_person:
                try:
                    contact = CustomerContact.objects.get(id=followup.contact_person.id)
                    followup.contact_number = contact.contact_detail          # phone
                    followup.designation = contact.customer.designation       # designation from Customer
                except CustomerContact.DoesNotExist:
                    pass

            followup.save()
            print(">>> FOLLOWUP SAVED:", followup.id, followup.company_name, followup.contact_person)  # debug
            return redirect("select_vist")  # success redirect (create URL)
        else:
            # ❌ FORM INVALID
            print(">>> FOLLOWUP FORM ERRORS:", form.errors)  # debug
    else:
        form = FollowUpForm()

    return render(request, "manager/new_followup.html", {"form": form})


# -------------------------------
# AJAX: Get contacts for a company (same as new visit)
# -------------------------------
@login_required
def get_followup_contacts(request, company_id):
    contacts = CustomerContact.objects.filter(customer_id=company_id)
    data = [
        {
            "id": c.id,
            "name": c.contact_name,
        }
        for c in contacts
    ]
    return JsonResponse({"contacts": data})


# -------------------------------
# AJAX: Get details for a contact (same as new visit)
# -------------------------------
@login_required
def get_followup_contact_details(request, contact_id):
    contact = get_object_or_404(CustomerContact, id=contact_id)
    data = {
        "contact_number": contact.contact_detail,           # from CustomerContact
        "designation": contact.customer.designation,        # from related Customer
    }
    return JsonResponse(data)







from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect
from django.contrib import messages

# The POSITION_CHOICES tuple
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

def login_user(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        # Authenticate with email as username (because USERNAME_FIELD = 'email')
        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)

            # Check user's position and redirect accordingly
            if user.position in ['Facilitator', 'Product Brand Manager', 'Zonal Sales Executive']:
                return redirect('add_visit')  # Redirect to 'index' for these positions
            elif user.position in ['Corporate Officer', 'Mobile Sales Officer', 'Desk Sales Officer']:
                return redirect('dashboard')  # Redirect to 'dashboard' for these positions
            else:
                return redirect('home')  # Default redirect for all other positions
        else:
            messages.error(request, 'Invalid email or password.')
            return redirect('login')

    # Handle GET request: Render the login page/form
    return render(request, 'auth/login.html')  # Ensure you have a 'login.html' template



from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
import re

User = get_user_model()

def register(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password = request.POST.get('password')
        password1 = request.POST.get('password1')
        position = request.POST.get('position')
        zone = request.POST.get('zone')
        branch = request.POST.get('branch')
        contact = request.POST.get('contact')

        # ✅ Password match check
        if password != password1:
            messages.error(request, "Passwords do not match.")
            return redirect('register')

        # ✅ Strong password custom rules
        if len(password) < 8:
            messages.error(request, "Password must be at least 8 characters long.")
            return redirect('register')
        if not re.search(r'[A-Z]', password):
            messages.error(request, "Password must contain at least one uppercase letter.")
            return redirect('register')
        if not re.search(r'[a-z]', password):
            messages.error(request, "Password must contain at least one lowercase letter.")
            return redirect('register')
        if not re.search(r'\d', password):
            messages.error(request, "Password must contain at least one digit.")
            return redirect('register')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            messages.error(request, "Password must contain at least one special character.")
            return redirect('register')

        # ✅ Django built-in password validation (optional but recommended)
        try:
            validate_password(password)
        except ValidationError as e:
            for error in e:
                messages.error(request, error)
            return redirect('register')

        # ✅ Email uniqueness check
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return redirect('register')

        # Tanzanian phone validation
        if not re.match(r'^(?:\+255|0)[67][1-9]\d{7}$', contact):
            messages.error(request, "Enter a valid Tanzanian phone number (e.g. +255712345678 or 0712345678).")
            return redirect('register')

        # ✅ First name + last name uniqueness check
        if User.objects.filter(first_name__iexact=first_name, last_name__iexact=last_name).exists():
            messages.error(request, "A user with this first and last name already exists.")
            return redirect('register')

        # ✅ Create user (without profile_picture)
        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            position=position,
            zone=zone,
            branch=branch,
            contact=contact
        )

        messages.success(request, "Account created successfully.")
        return redirect('login')

    return render(request, 'auth/register.html')



def logout_user(request):
    if request.user.is_authenticated:
        logout(request)
        return redirect('login')
    else:
        messages.error(request,'You must login first to access the page')
        return redirect('login')


from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.utils.timezone import localdate
from .models import DailyVisitForm

@login_required
def daily_forms_list(request):
    today = localdate()
    forms = DailyVisitForm.objects.filter(user=request.user).order_by('-created_at')
    return render(
        request,
        "manager/daily_submissions_list.html",
        {"forms": forms, "today": today}
    )

import requests
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import DailyVisitForm


def get_location_name(lat, lon):
    """Reverse geocode coordinates using OpenStreetMap Nominatim API."""
    try:
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {
            "lat": lat,
            "lon": lon,
            "format": "json",
            "zoom": 10,
            "addressdetails": 1
        }
        headers = {
            "User-Agent": "my_visits_app_ando_2025"  # custom identifier
        }
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "address" in data:
                addr = data["address"]
                return {
                    "place_name": data.get("display_name", "Unknown"),
                    "region": addr.get("state", ""),
                    "zone": addr.get("county", ""),
                    "nation": addr.get("country", "")
                }
        return {"place_name": "Unknown", "region": "", "zone": "", "nation": ""}
    except Exception as e:
        print(f"Reverse geocode error: {e}")
        return {"place_name": "Unknown", "region": "", "zone": "", "nation": ""}


@login_required
def daily_form_detail(request, pk):
    form = get_object_or_404(DailyVisitForm, pk=pk, user=request.user)
    visits = form.visits.all()

    # Add location info for each visit
    for v in visits:
        if v.latitude and v.longitude:
            loc = get_location_name(v.latitude, v.longitude)
            v.place_name = loc["place_name"]
            v.region = loc["region"]
            v.zone = loc["zone"]
            v.nation = loc["nation"]
        else:
            v.place_name = "Not Available"
            v.region = ""
            v.zone = ""
            v.nation = ""

    return render(
        request,
        "manager/submission_detail.html",
        {"form": form, "visits": visits}
    )




from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.timezone import localdate
from .models import DailyFollowUp


@login_required
def daily_followups_list(request):
    today = localdate()
    forms = (
        DailyFollowUp.objects.filter(user=request.user)
        .select_related("submission")
        .order_by("-created_at")
    )
    return render(
        request,
        "manager/daily_followup_list.html",  # 🔑 separate template for followups
        {"forms": forms, "today": today},
    )



import requests
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import DailyFollowUp


def get_location_name(lat, lon):
    """Reverse geocode coordinates using OpenStreetMap Nominatim API."""
    try:
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {
            "lat": lat,
            "lon": lon,
            "format": "json",
            "zoom": 10,
            "addressdetails": 1
        }
        headers = {
            "User-Agent": "my_followup_app_ando_2025"  # custom identifier
        }
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "address" in data:
                addr = data["address"]
                return {
                    "place_name": data.get("display_name", "Unknown"),
                    "region": addr.get("state", ""),
                    "zone": addr.get("county", ""),
                    "nation": addr.get("country", "")
                }
        return {"place_name": "Unknown", "region": "", "zone": "", "nation": ""}
    except Exception as e:
        print(f"Reverse geocode error: {e}")
        return {"place_name": "Unknown", "region": "", "zone": "", "nation": ""}


@login_required
def daily_followup_detail(request, pk):
    form = get_object_or_404(DailyFollowUp, pk=pk, user=request.user)
    followups = form.followups.all()  # ✅ related_name from model

    # Add location info for each followup
    for f in followups:
        if f.latitude and f.longitude:
            loc = get_location_name(f.latitude, f.longitude)
            f.place_name = loc["place_name"]
            f.region = loc["region"]
            f.zone = loc["zone"]
            f.nation = loc["nation"]
        else:
            f.place_name = "Not Available"
            f.region = ""
            f.zone = ""
            f.nation = ""

    return render(
        request,
        "manager/followup_detail.html",  # 🔑 separate template
        {"form": form, "followups": followups}
    )



import requests
from django.core.paginator import Paginator
from django.utils.dateparse import parse_date
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Sum, Count   # ✅ add this
from .models import NewVisit


def get_location_name(lat, lon):
    """Reverse geocode coordinates using OpenStreetMap Nominatim API."""
    try:
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {
            "lat": lat,
            "lon": lon,
            "format": "json",
            "zoom": 10,
            "addressdetails": 1,
        }
        headers = {
            "User-Agent": "my_visits_app_ando_2025"
        }
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "address" in data:
                addr = data["address"]
                return {
                    "place_name": data.get("display_name", "Unknown"),
                    "region": addr.get("state", ""),
                    "zone": addr.get("county", ""),
                    "nation": addr.get("country", ""),
                }
        return {"place_name": "Unknown", "region": "", "zone": "", "nation": ""}
    except Exception as e:
        print(f"Reverse geocode error: {e}")
        return {"place_name": "Unknown", "region": "", "zone": "", "nation": ""}


@login_required
def all_visit_list(request):
    created_date = request.GET.get("created_date")
    visits_qs = (
        NewVisit.objects.filter(daily_form__user=request.user)
        .order_by("-created_at")
    )

    # Filter if created_date provided
    if created_date:
        parsed_date = parse_date(created_date)
        if parsed_date:
            visits_qs = visits_qs.filter(created_at__date=parsed_date)

    # ✅ Calculate totals for quoted orders
    totals = visits_qs.filter(is_order_quoted=True).aggregate(
        total_amount=Sum("order_amount"),
        total_count=Count("id")
    )
    total_order_amount = totals["total_amount"] or 0
    total_quoted_count = totals["total_count"] or 0

    # Enrich each visit with location info
    for v in visits_qs:
        if v.latitude and v.longitude:
            loc = get_location_name(v.latitude, v.longitude)
            v.place_name = loc["place_name"]
            v.region = loc["region"]
            v.zone = loc["zone"]
            v.nation = loc["nation"]
        else:
            v.place_name = "Not Available"
            v.region = ""
            v.zone = ""
            v.nation = ""

    # Pagination (20 visits per page)
    paginator = Paginator(visits_qs, 20)
    page_number = request.GET.get("page")
    visits = paginator.get_page(page_number)

    return render(
        request,
        "manager/all_visit_list.html",
        {
            "visits": visits,
            "created_date": created_date,
            "total_order_amount": total_order_amount,   # ✅ pass total
            "total_quoted_count": total_quoted_count,   # ✅ pass count
        },
    )



import io
import requests
from decimal import Decimal
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils.dateparse import parse_date
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from .models import NewVisit
from xhtml2pdf import pisa


def get_location_name(lat, lon):
    """Reverse geocode coordinates using OpenStreetMap Nominatim API."""
    try:
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {"lat": lat, "lon": lon, "format": "json", "zoom": 10, "addressdetails": 1}
        headers = {"User-Agent": "my_visits_app_pdf_2025"}
        r = requests.get(url, params=params, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            addr = data.get("address", {})
            return {
                "place_name": data.get("display_name", "Unknown"),
                "region": addr.get("state", ""),
                "zone": addr.get("county", ""),
                "nation": addr.get("country", ""),
            }
    except Exception:
        pass
    return {"place_name": "Unknown", "region": "", "zone": "", "nation": ""}


@login_required
def export_visits_pdf(request):
    """Export visits to PDF with totals and location info (Windows-friendly)."""
    created_date = request.GET.get("created_date")
    visits_qs = NewVisit.objects.filter(daily_form__user=request.user).order_by("-created_at")

    # Filter by date
    if created_date:
        parsed_date = parse_date(created_date)
        if parsed_date:
            visits_qs = visits_qs.filter(created_at__date=parsed_date)

    # Totals for quoted orders
    totals = visits_qs.filter(is_order_quoted=True).aggregate(
        total_amount=Sum("order_amount"),
        total_count=Count("id"),
    )
    total_quoted_count = totals.get("total_count") or 0

    # Handle None total_amount gracefully
    if totals.get("total_amount") is None:
        def to_decimal(x):
            try:
                return Decimal(str(x or "0").replace(",", ""))
            except Exception:
                return Decimal("0")

        total_order_amount = sum(
            (to_decimal(v.order_amount) for v in visits_qs.filter(is_order_quoted=True)),
            Decimal("0"),
        )
    else:
        total_order_amount = totals["total_amount"]

    # Add location info per record
    for v in visits_qs:
        if v.latitude and v.longitude:
            loc = get_location_name(v.latitude, v.longitude)
            v.place_name = loc["place_name"]
            v.region = loc["region"]
            v.zone = loc["zone"]
            v.nation = loc["nation"]
        else:
            v.place_name = "Not Available"
            v.region = v.zone = v.nation = ""

    # Render HTML template
    html = render_to_string(
        "manager/visits_pdf.html",
        {
            "visits": visits_qs,
            "created_date": created_date,
            "total_order_amount": total_order_amount,
            "total_quoted_count": total_quoted_count,
        },
    )

    # Convert HTML → PDF with xhtml2pdf (pisa)
    result = io.BytesIO()
    pisa_status = pisa.CreatePDF(
        html,
        dest=result,
        encoding="utf-8"
    )

    if pisa_status.err:
        return HttpResponse("Error generating PDF", status=500)

    filename = f'visits{"_" + created_date if created_date else ""}.pdf'
    response = HttpResponse(result.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    response["X-Content-Type-Options"] = "nosniff"
    response["Cache-Control"] = "no-store"
    return response



import requests
from django.core.paginator import Paginator
from django.utils.dateparse import parse_date
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Sum, Count, Q
from .models import FollowUp


def get_location_name(lat, lon):
    """Reverse geocode coordinates using OpenStreetMap Nominatim API."""
    try:
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {"lat": lat, "lon": lon, "format": "json", "zoom": 10, "addressdetails": 1}
        headers = {"User-Agent": "my_visits_app_ando_2025"}
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "address" in data:
                addr = data["address"]
                return {
                    "place_name": data.get("display_name", "Unknown"),
                    "region": addr.get("state", ""),
                    "zone": addr.get("county", ""),
                    "nation": addr.get("country", ""),
                }
        return {"place_name": "Unknown", "region": "", "zone": "", "nation": ""}
    except Exception as e:
        print(f"Reverse geocode error: {e}")
        return {"place_name": "Unknown", "region": "", "zone": "", "nation": ""}


@login_required
def daily_followup_listing(request):
    created_date = request.GET.get("created_date")

    followups_qs = FollowUp.objects.filter(added_by=request.user)

    if created_date:
        parsed_date = parse_date(created_date)
        if parsed_date:
            followups_qs = followups_qs.filter(created_at__date=parsed_date)

    followups_qs = followups_qs.select_related(
        'company_name', 'contact_person', 'daily_followup'
    ).order_by("-created_at")

    # ✅ Extended Totals
    totals = followups_qs.aggregate(
        total_order_amount=Sum("order_amount"),
        total_payment_collected=Sum("payment_amount"),
        total_followups=Count("id"),
        count_order_quoted=Count("id", filter=Q(is_order_quoted=True)),
        count_payment_collected=Count("id", filter=Q(is_payment_collected=True)),
    )

    # ✅ Add location info to each followup
    for f in followups_qs:
        if f.latitude and f.longitude:
            loc = get_location_name(f.latitude, f.longitude)
            f.place_name = loc["place_name"]
            f.region = loc["region"]
            f.zone = loc["zone"]
            f.nation = loc["nation"]
        else:
            f.place_name = None
            f.region = ""
            f.zone = ""
            f.nation = ""

    # ✅ Pagination
    paginator = Paginator(followups_qs, 20)
    page_number = request.GET.get("page")
    followups = paginator.get_page(page_number)

    return render(
        request,
        "manager/daily_followups_list.html",
        {
            "followups": followups,
            "created_date": created_date,
            "total_order_amount": totals["total_order_amount"] or 0,
            "total_payment_collected": totals["total_payment_collected"] or 0,
            "total_followups": totals["total_followups"] or 0,
            "count_order_quoted": totals["count_order_quoted"] or 0,
            "count_payment_collected": totals["count_payment_collected"] or 0,
        },
    )



import io
import requests
from decimal import Decimal
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils.dateparse import parse_date
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q
from xhtml2pdf import pisa
from .models import FollowUp

def get_location_name(lat, lon):
    try:
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {"lat": lat, "lon": lon, "format": "json", "zoom": 10, "addressdetails": 1}
        headers = {"User-Agent": "my_followups_pdf_2025"}
        r = requests.get(url, params=params, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            addr = data.get("address", {})
            return {
                "place_name": data.get("display_name", "Unknown"),
                "region": addr.get("state", ""),
                "zone": addr.get("county", ""),
                "nation": addr.get("country", ""),
            }
    except Exception:
        pass
    return {"place_name": "Unknown", "region": "", "zone": "", "nation": ""}

@login_required
def export_followups_pdf(request):
    created_date = request.GET.get("created_date")
    followups_qs = FollowUp.objects.filter(added_by=request.user).order_by("-created_at")

    if created_date:
        parsed_date = parse_date(created_date)
        if parsed_date:
            followups_qs = followups_qs.filter(created_at__date=parsed_date)

    totals = followups_qs.aggregate(
        total_order_amount=Sum("order_amount"),
        total_payment_collected=Sum("payment_amount"),
        total_followups=Count("id"),
        count_order_quoted=Count("id", filter=Q(is_order_quoted=True)),
        count_payment_collected=Count("id", filter=Q(is_payment_collected=True)),
    )

    # Add location data
    for f in followups_qs:
        if f.latitude and f.longitude:
            loc = get_location_name(f.latitude, f.longitude)
            f.place_name = loc["place_name"]
            f.region = loc["region"]
            f.zone = loc["zone"]
            f.nation = loc["nation"]
        else:
            f.place_name = "Not Available"
            f.region = f.zone = f.nation = ""

    # Render HTML
    html = render_to_string("manager/followups_pdf.html", {
        "followups": followups_qs,
        "created_date": created_date,
        "total_order_amount": totals["total_order_amount"] or 0,
        "total_payment_collected": totals["total_payment_collected"] or 0,
        "total_followups": totals["total_followups"] or 0,
        "count_order_quoted": totals["count_order_quoted"] or 0,
        "count_payment_collected": totals["count_payment_collected"] or 0,
    })

    # Convert to PDF
    result = io.BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=result, encoding="utf-8")

    if pisa_status.err:
        return HttpResponse("PDF generation failed", status=500)

    filename = f'followups{"_" + created_date if created_date else ""}.pdf'
    response = HttpResponse(result.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
