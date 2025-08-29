from django.urls import path
from . import views

urlpatterns = [
    path("add/", views.add_customer, name="add_customer"),
    path("list/", views.customer_list, name="customer_list"),
     path("customers/<int:pk>/update/", views.update_customer, name="update_customer"),
    path("delete/<int:pk>/", views.delete_customer, name="delete_customer"),
    path('customers/<int:customer_id>/view/', views.view_customer, name='view_customer'),
    path('customer/<int:customer_id>/pdf/', views.export_customer_detail_pdf, name='customer_detail_pdf'),
]




