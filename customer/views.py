from django.shortcuts import render, redirect
from django.forms import modelformset_factory
from .forms import CustomerForm, CustomerContactForm
from .models import Customer, CustomerContact

# Use a plain ModelFormSet for adding contacts
ContactFormSet = modelformset_factory(
    CustomerContact,
    form=CustomerContactForm,
    extra=1,          # at least one empty row
    can_delete=True
)

def add_customer(request):
    if request.method == "POST":
        customer_form = CustomerForm(request.POST)
        # IMPORTANT: use the SAME prefix for GET and POST
        formset = ContactFormSet(request.POST, queryset=CustomerContact.objects.none(), prefix="contacts")

        if customer_form.is_valid() and formset.is_valid():
            # Save parent first
            customer = customer_form.save()

            # Save contacts and attach the customer
            contacts = formset.save(commit=False)
            for c in contacts:
                c.customer = customer
                c.save()

            # Handle deletes (if any were added then removed)
            for obj in formset.deleted_objects:
                obj.delete()

            return redirect("customer_list")

    else:
        customer_form = CustomerForm()
        # Same prefix in GET; start with no contacts from DB
        formset = ContactFormSet(queryset=CustomerContact.objects.none(), prefix="contacts")

    return render(request, "manager/add_customer.html", {
        "customer_form": customer_form,
        "formset": formset,
        "is_update": False,   # just for your heading/buttons
    })


from django.shortcuts import render
from django.db.models import Q
from .models import Customer

def customer_list(request):
    query = request.GET.get("q", "")
    customers = Customer.objects.prefetch_related("contacts").all()

    if query:
        customers = customers.filter(
            Q(company_name__icontains=query) |
            Q(designation__icontains=query)
        )

    context = {
        "customers": customers,
        "query": query,
    }
    return render(request, "manager/customer_list.html", context)


from django.shortcuts import render, get_object_or_404, redirect
from django.forms import inlineformset_factory
from django.contrib import messages
from .models import Customer, CustomerContact
from .forms import CustomerForm, CustomerContactForm


def update_customer(request, pk):
    customer = get_object_or_404(Customer, pk=pk)

    # Inline formset for contacts tied to customer
    ContactFormSet = inlineformset_factory(
        Customer,
        CustomerContact,
        form=CustomerContactForm,
        extra=0,          # no blank rows by default
        can_delete=True   # allow delete
    )

    if request.method == "POST":
        customer_form = CustomerForm(request.POST, instance=customer)
        formset = ContactFormSet(request.POST, instance=customer)

        if customer_form.is_valid() and formset.is_valid():
            customer_form.save()
            formset.save()  # updates, deletes, and adds new
            messages.success(request, "✅ Customer updated successfully!")
            return redirect("customer_list")
        else:
            print("❌ FORM ERRORS:", customer_form.errors, formset.errors)
    else:
        customer_form = CustomerForm(instance=customer)
        formset = ContactFormSet(instance=customer)

    return render(request, "manager/update_customer.html", {
        "customer_form": customer_form,
        "formset": formset,
        "customer": customer,
    })



# ✅ DELETE CUSTOMER
def delete_customer(request, pk):
    customer = get_object_or_404(Customer, pk=pk)

    if request.method == "POST":
        customer.delete()
        messages.success(request, "🗑️ Customer deleted successfully!")
        return redirect("customer_list")

    return render(request, "manager/customer_confirm_delete.html", {"customer": customer})


from django.shortcuts import render, get_object_or_404
from .models import Customer, CustomerContact
from visits.models import NewVisit, FollowUp  # adjust path if needed

from django.db.models import Sum

def view_customer(request, customer_id):
    customer = Customer.objects.get(pk=customer_id)
    contacts = customer.contacts.all()

    # New Visit Quoted Orders
    quoted_visits = customer.visits.filter(is_order_quoted=True)
    quoted_visits_total = quoted_visits.aggregate(total=Sum('order_amount'))['total'] or 0

    # Follow-up Orders and Payments
    followups = customer.followups.all()
    followup_order_total = followups.filter(is_order_quoted=True).aggregate(total=Sum('order_amount'))['total'] or 0
    followup_payment_total = followups.filter(is_payment_collected=True).aggregate(total=Sum('payment_amount'))['total'] or 0

    return render(request, 'manager/customer_detail.html', {
        'customer': customer,
        'contacts': contacts,
        'quoted_visits': quoted_visits,
        'quoted_visits_total': quoted_visits_total,
        'followups': followups,
        'followup_order_total': followup_order_total,
        'followup_payment_total': followup_payment_total,
    })



import io
from django.http import HttpResponse
from django.template.loader import render_to_string
from xhtml2pdf import pisa
from django.shortcuts import get_object_or_404
from django.db.models import Sum
from .models import Customer

def export_customer_detail_pdf(request, customer_id):
    customer = get_object_or_404(Customer, pk=customer_id)
    contacts = customer.contacts.all()

    quoted_visits = customer.visits.filter(is_order_quoted=True)
    quoted_visits_total = quoted_visits.aggregate(total=Sum('order_amount'))['total'] or 0

    followups = customer.followups.all()
    followup_order_total = followups.filter(is_order_quoted=True).aggregate(total=Sum('order_amount'))['total'] or 0
    followup_payment_total = followups.filter(is_payment_collected=True).aggregate(total=Sum('payment_amount'))['total'] or 0

    # Render your existing template to HTML string
    html = render_to_string('manager/customer_detail_pdf.html', {
        'customer': customer,
        'contacts': contacts,
        'quoted_visits': quoted_visits,
        'quoted_visits_total': quoted_visits_total,
        'followups': followups,
        'followup_order_total': followup_order_total,
        'followup_payment_total': followup_payment_total,
    })

    result = io.BytesIO()
    pdf_status = pisa.CreatePDF(io.BytesIO(html.encode('utf-8')), dest=result, encoding='utf-8')

    if pdf_status.err:
        return HttpResponse('Error generating PDF', status=500)

    response = HttpResponse(result.getvalue(), content_type='application/pdf')
    filename = f'{customer.company_name}_detail.pdf'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    return response
