from django.urls import path
from . import views

urlpatterns = [

    path('', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('register/', views.register, name='register'),
      path('new_visit/', views.new_visit, name='new_visit'),
    path('select-visit/', views.select_visit, name='select_vist'),
    path('add-visit/', views.add_visit, name='add_visit'),
    path('dashboard/', views.index, name='dashboard'),  # You can replace 'index' with a real dashboard view later
    path('data-entry-home/', views.index, name='index'),
   path("daily-submissions/", views.daily_forms_list, name="daily_forms_list"),
   path("daily_followups_list/", views.daily_followups_list, name="daily_followups_list"),
   path(
        "followup/<int:pk>/",
        views.daily_followup_detail,
        name="daily_followup_detail"
    ),
    path("daily-followups/pdf/", views.export_followups_pdf, name="export_followups_pdf"),

    path("get-contacts/<int:company_id>/", views.get_contacts, name="get_contacts"),
    path("get-contact-details/<int:contact_id>/", views.get_contact_details, name="get_contact_details"),
     path("daily-followups_listing/", views.daily_followup_listing, name="daily_followup_listing"),  # n
    path("submission/<int:pk>/", views.daily_form_detail, name="submission_detail"),
     path('new_followup/', views.new_followup, name='new_followup'),
     path("all-visits/pdf/", views.export_visits_pdf, name="export_visits_pdf"),
     path('all_visits/', views.all_visit_list, name='all_visit_list'),# You can replace 'index' with a home view too
]
