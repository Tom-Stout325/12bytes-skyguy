from django.urls import path
from .views import *


urlpatterns = [
    # Dashboard
    path('dashboard', Dashboard.as_view(), name='dashboard'),

    # Transactions
    path('transactions/', Transactions.as_view(), name="transactions"),
    path('transactions/download/', DownloadTransactionsCSV.as_view(), name="download_transactions_csv"),
    path('transaction/new', TransactionCreateView.as_view(), name="add_transaction"),
    path('transaction/success', add_transaction_success, name='add_transaction_success'),
    path('transaction/<int:pk>/', TransactionDetailView.as_view(), name='transaction_detail'),
    path('transaction/edit/<int:pk>/', TransactionUpdateView.as_view(), name='edit_transaction'),
    path('transaction/delete/<int:pk>/', TransactionDeleteView.as_view(), name='delete_transaction'),

    # Invoices
    path('invoices/', InvoiceListView.as_view(), name='invoice_list'),
    path('invoices/<int:pk>/delete/', InvoiceDeleteView.as_view(), name='invoice_delete'),
    path('invoice/<int:pk>/', InvoiceDetailView.as_view(), name='invoice_detail'),
    path('invoice/<int:pk>/review/', invoice_review, name='invoice_review'),
    path('invoice/<int:pk>/pdf/', invoice_review_pdf, name='invoice_review_pdf'),
    path('invoice/new', InvoiceCreateView.as_view(), name='create_invoice'),
    path('invoice/edit/<int:pk>/', InvoiceUpdateView.as_view(), name='update_invoice'),
    path('invoice/<int:invoice_id>/email/', send_invoice_email, name='send_invoice_email'),
    path('unpaid-invoices/', unpaid_invoices, name='unpaid_invoices'),
    path('invoices/export/csv/', export_invoices_csv, name='export_invoices_csv'),
    path('invoices/export/pdf/', export_invoices_pdf, name='export_invoices_pdf'),

    # Categories & Subcategories
    path('category-report/', CategoryListView.as_view(), name='category_page'),
    path('category/add/', CategoryCreateView.as_view(), name='add_category'),
    path('category/edit/<int:pk>/', CategoryUpdateView.as_view(), name='edit_category'),
    path('category/delete/<int:pk>/', CategoryDeleteView.as_view(), name='delete_category'),
    path('sub_category/add/', SubCategoryCreateView.as_view(), name='add_sub_category'),
    path('sub_category/edit/<int:pk>/', SubCategoryUpdateView.as_view(), name='edit_sub_category'),
    path('sub_category/delete/<int:pk>/', SubCategoryDeleteView.as_view(), name='delete_sub_category'),

    # Clients
    path('clients/', ClientListView.as_view(), name='client_list'),
    path('clients/add/', ClientCreateView.as_view(), name='add_client'),
    path('clients/edit/<int:pk>/', ClientUpdateView.as_view(), name='edit_client'),
    path('client/delete/<int:pk>/', ClientDeleteView.as_view(), name='delete_client'),

    # Reports
    path('reports/', reports_page, name='reports'),
    path('financial-statement/', financial_statement, name='financial_statement'),
    path('finance/financial-statement/pdf/<int:year>/', financial_statement_pdf, name='financial_statement_pdf'),
    path('category-summary/', category_summary, name='category_summary'),
    path('finance/category-summary/pdf/', category_summary_pdf, name='category_summary_pdf'),

    # Mileage
    path('mileage-log/', mileage_log, name='mileage_log'),
    path('mileage/add/', MileageCreateView.as_view(), name='mileage_create'),
    path('mileage/<int:pk>/edit/', MileageUpdateView.as_view(), name='mileage_update'),
    path('mileage/<int:pk>/delete/', MileageDeleteView.as_view(), name='mileage_delete'),
    path('mileage/update-rate/', update_mileage_rate, name='update_mileage_rate'),
      
    # Services
    path('services/', service_list, name='service_list'),
    path('services/add/', service_create, name='service_create'),
    path('services/<int:pk>/edit/', service_update, name='service_update'),
    path('services/<int:pk>/delete/', service_delete, name='service_delete'),
]