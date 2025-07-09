from django.views.generic import TemplateView, ListView, DetailView, UpdateView, DeleteView, CreateView
from django.http import JsonResponse, HttpResponse, StreamingHttpResponse
from django.db.models import Sum, Q, F, ExpressionWrapper, DecimalField
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib.postgres.indexes import GinIndex
from django.template.loader import render_to_string
from django.db.models.functions import ExtractYear
from django.template.loader import get_template
from django.urls import reverse_lazy, reverse
from django.core.paginator import Paginator
from calendar import monthrange, month_name
from decimal import Decimal, ROUND_HALF_UP
from django.core.mail import EmailMessage
from django.utils.timezone import now
from django.contrib import messages
from collections import defaultdict
from datetime import datetime, date
from django.db import transaction
from django.utils import timezone
from django.conf import settings
from django.views import View
from weasyprint import HTML
from pathlib import Path
import tempfile
import logging
import csv
import os
from .models import *
from .forms import *


logger = logging.getLogger(__name__)

# Dashboard
class Dashboard(LoginRequiredMixin, TemplateView):
    template_name = "finance/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_page'] = 'dashboard'
        return context

# ---------------------------------------------------------------------------------------------------------------   Transactions

class Transactions(LoginRequiredMixin, ListView):
    model = Transaction
    template_name = "finance/transactions.html"
    context_object_name = "transactions"
    paginate_by = 50

    def get_queryset(self):
        queryset = Transaction.objects.select_related(
            'category', 'sub_cat',
        ).filter(user=self.request.user)

        category_id = self.request.GET.get('category')
        if category_id and Category.objects.filter(id=category_id).exists():
            queryset = queryset.filter(category__id=category_id)

        sub_cat_id = self.request.GET.get('sub_cat')
        if sub_cat_id and SubCategory.objects.filter(id=sub_cat_id).exists():
            queryset = queryset.filter(sub_cat__id=sub_cat_id)

        year = self.request.GET.get('year')
        if year and year.isdigit() and 1900 <= int(year) <= 9999:
            queryset = queryset.filter(date__year=year)

        sort = self.request.GET.get('sort', '-date')
        valid_sort_fields = [
            'date', '-date', 
            'trans_type', '-trans_type',
            'transaction', '-transaction',
            'amount', '-amount', 
            'invoice_numb', '-invoice_numb'
        ]
        if sort in valid_sort_fields:
            queryset = queryset.order_by(sort)
        else:
            queryset = queryset.order_by('-date')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_sort'] = self.request.GET.get('sort', '-date')
        context['categories'] = Category.objects.filter(transaction__isnull=False, transaction__user=self.request.user).distinct().order_by('category')
        context['subcategories'] = SubCategory.objects.filter(transaction__isnull=False, transaction__user=self.request.user).distinct().order_by('sub_cat')
        context['years'] = [str(y) for y in Transaction.objects.filter(user=self.request.user).annotate(
        extracted_year=ExtractYear('date')).values_list('extracted_year', flat=True).distinct().order_by('-extracted_year') if y]
        context['selected_category'] = self.request.GET.get('category', '')
        context['selected_sub_cat'] = self.request.GET.get('sub_cat', '')
        context['selected_year'] = self.request.GET.get('year', '')
        context['current_page'] = 'transactions'
        return context



class Echo:
    def write(self, value):
        return value

class DownloadTransactionsCSV(LoginRequiredMixin, View):
    def get(self, request):
        try:
            # Get base queryset
            if request.GET.get('all') == 'true':
                queryset = Transaction.objects.filter(user=request.user)
            else:
                transactions_view = Transactions()
                transactions_view.request = request
                queryset = transactions_view.get_queryset()

            # Filter by year
            year = request.GET.get('year')
            if year and year.isdigit():
                queryset = queryset.filter(date__year=int(year))

            # Debug check
            if not queryset.exists():
                logger.warning(f"No transactions found for user {request.user} in export.")
                return HttpResponse("No transactions to export.", status=204)

            print("Transaction count:", queryset.count())
            logger.info(f"Transaction count for {request.user}: {queryset.count()}")

            # CSV generator
            def stream_csv(queryset):
                pseudo_buffer = Echo()
                writer = csv.writer(pseudo_buffer)
                yield writer.writerow(['Date', 'Type', 'Transaction', 'Location', 'Amount', 'Invoice #'])
                for tx in queryset.iterator():
                    yield writer.writerow([
                        tx.date,
                        tx.trans_type or '',
                        tx.transaction,
                        tx.amount,
                        tx.invoice_numb or ''
                    ])

            # Determine filename
            if request.GET.get('all') == 'true':
                filename = "all_transactions.csv"
            elif year and year.isdigit():
                filename = f"transactions_{year}.csv"
            else:
                filename = "transactions.csv"

            # Return streaming response
            response = StreamingHttpResponse(stream_csv(queryset), content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response

        except Exception as e:
            logger.error(f"Error generating CSV for user {request.user.id}: {e}")
            return HttpResponse("Error generating CSV", status=500)



class TransactionCreateView(LoginRequiredMixin, CreateView):
    model = Transaction
    form_class = TransactionsForm
    template_name = 'finance/transaction_add.html'
    success_url = reverse_lazy('add_transaction_success')

    def form_valid(self, form):
        form.instance.user = self.request.user
        try:
            with transaction.atomic():
                response = super().form_valid(form)
                messages.success(self.request, 'Transaction added successfully!')
                return response
        except Exception as e:
            logger.error(f"Error adding transaction for user {self.request.user.id}: {e}")
            messages.error(self.request, 'Error adding transaction. Please check the form.')
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_page'] = 'transactions'

        form = context.get('form')
        sub_cat_id = self.request.POST.get('sub_cat') or self.request.GET.get('sub_cat')
        if sub_cat_id:
            from finance.models import SubCategory
            try:
                selected_category = SubCategory.objects.get(pk=sub_cat_id).category
                context['selected_category'] = selected_category
            except SubCategory.DoesNotExist:
                context['selected_category'] = None

        return context



class TransactionUpdateView(LoginRequiredMixin, UpdateView):
    model = Transaction
    form_class = TransactionsForm
    template_name = 'finance/transaction_edit.html'
    success_url = reverse_lazy('transactions')

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)

    def form_valid(self, form):
        try:
            with transaction.atomic():
                response = super().form_valid(form)
                messages.success(self.request, 'Transaction updated successfully!')
                return response
        except Exception as e:
            logger.error(f"Error updating transaction {self.get_object().id} for user {self.request.user.id}: {e}")
            messages.error(self.request, 'Error updating transaction. Please check the form.')
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_page'] = 'transactions'

        sub_cat = self.object.sub_cat
        if sub_cat:
            context['selected_category'] = sub_cat.category

        return context



class TransactionDeleteView(LoginRequiredMixin, DeleteView):
    model = Transaction
    template_name = "finance/transaction_confirm_delete.html"
    success_url = reverse_lazy('transactions')

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)

    def delete(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                response = super().delete(request, *args, **kwargs)
                messages.success(self.request, "Transaction deleted successfully!")
                return response
        except models.ProtectedError:
            messages.error(self.request, "Cannot delete transaction due to related records.")
            return redirect('transactions')
        except Exception as e:
            logger.error(f"Error deleting transaction for user {request.user.id}: {e}")
            messages.error(self.request, "Error deleting transaction.")
            return redirect('transactions')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_page'] = 'transactions'
        return context


class TransactionDetailView(LoginRequiredMixin, DetailView):
    model = Transaction
    template_name = 'finance/transactions_detail_view.html'
    context_object_name = 'transaction'

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_page'] = 'transactions'
        return context


@login_required
def add_transaction_success(request):
    context = {'current_page': 'transactions'}
    return render(request, 'finance/transaction_add_success.html', context)


# ---------------------------------------------------------------------------------------------------------------  Invoices


class InvoiceCreateView(LoginRequiredMixin, CreateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = 'finance/invoice_add.html'
    success_url = reverse_lazy('invoice_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['formset'] = InvoiceItemFormSet(self.request.POST or None)
        context['current_page'] = 'invoices'
        return context

    def form_valid(self, form):
        formset = InvoiceItemFormSet(self.request.POST)
        if formset.is_valid():
            try:
                with transaction.atomic():
                    invoice = form.save(commit=False)
                    invoice.amount = 0
                    invoice.save()
                    for item_form in formset:
                        if item_form.cleaned_data and not item_form.cleaned_data.get('DELETE', False):
                            item = item_form.save(commit=False)
                            item.invoice = invoice
                            item.save()
                    invoice.amount = invoice.items.aggregate(total=Sum('price'))['total'] or 0
                    invoice.save()
                    messages.success(self.request, f"Invoice #{invoice.invoice_numb} created successfully.")
                    return super().form_valid(form)
            except Exception as e:
                logger.error(f"Error creating invoice for user {self.request.user.id}: {e}")
                messages.error(self.request, "Error creating invoice. Please check the form.")
                return self.form_invalid(form)
        else:
            logger.error(f"Formset errors for invoice creation: {formset.errors}")
            messages.error(self.request, "Error in invoice items. Please check the form.")
            return self.form_invalid(form)


class InvoiceUpdateView(LoginRequiredMixin, UpdateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = 'finance/invoice_update.html'
    success_url = reverse_lazy('invoice_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['formset'] = InvoiceItemFormSet(self.request.POST or None, instance=self.object)
        context['invoice'] = self.object
        context['current_page'] = 'invoices'
        return context

    def form_valid(self, form):
        formset = InvoiceItemFormSet(self.request.POST, instance=self.object)
        if formset.is_valid():
            try:
                with transaction.atomic():
                    form.save()
                    formset.save()
                    invoice = self.object
                    invoice.amount = invoice.items.aggregate(total=Sum('price'))['total'] or 0
                    invoice.save()
                    messages.success(self.request, f"Invoice #{invoice.invoice_numb} updated successfully.")
                    return super().form_valid(form)
            except Exception as e:
                logger.error(f"Error updating invoice {self.object.id} for user {self.request.user.id}: {e}")
                messages.error(self.request, "Error updating invoice. Please check the form.")
                return self.form_invalid(form)
        else:
            logger.error(f"Formset errors for invoice update: {formset.errors}")
            messages.error(self.request, "Error in invoice items. Please check the form.")
            return self.form_invalid(form)


class InvoiceListView(LoginRequiredMixin, ListView):
    model = Invoice
    template_name = "finance/invoices.html"
    context_object_name = "invoices"
    paginate_by = 20

    def get_queryset(self):
        sort = self.request.GET.get('sort', 'invoice_numb')
        direction = self.request.GET.get('direction', 'desc')
        valid_sort_fields = [
            'invoice_numb', 'client__business', 'service__service',
            'amount', 'date', 'due', 'paid_date', 'days_to_pay'
        ]
        if sort not in valid_sort_fields:
            sort = 'invoice_numb'
        ordering = f"-{sort}" if direction == 'desc' else sort
        queryset = Invoice.objects.select_related('client', 'service').prefetch_related('items').order_by(ordering)
        search_query = self.request.GET.get('search', '')
        if search_query:
            if len(search_query) > 100:  # Prevent abuse
                search_query = search_query[:100]
            queryset = queryset.filter(
                search_vector=search_query
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['current_sort'] = self.request.GET.get('sort', 'invoice_numb')
        context['current_direction'] = self.request.GET.get('direction', 'desc')
        context['current_page'] = 'invoices'
        return context


class InvoiceDetailView(LoginRequiredMixin, DetailView):
    model = Invoice
    template_name = 'finance/invoice_detail.html'
    context_object_name = 'invoice'

    def get_queryset(self):
        return Invoice.objects.select_related('client', 'service').prefetch_related('items')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        logo_path = next((
            os.path.join(path, 'images/logo2.png')
            for path in (settings.STATICFILES_DIRS if hasattr(settings, 'STATICFILES_DIRS') else [])
            if os.path.exists(os.path.join(path, 'images/logo2.png'))
        ), None)
        context['logo_path'] = f'file://{logo_path}' if logo_path and os.path.exists(logo_path) else None
        context['rendering_for_pdf'] = self.request.GET.get('pdf', False)
        context['current_page'] = 'invoices'
        return context


class InvoiceDeleteView(LoginRequiredMixin, DeleteView):
    model = Invoice
    template_name = "finance/invoice_confirm_delete.html"
    success_url = reverse_lazy('invoice_list')

    def delete(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                response = super().delete(request, *args, **kwargs)
                messages.success(self.request, "Invoice deleted successfully.")
                return response
        except models.ProtectedError:
            messages.error(self.request, "Cannot delete invoice due to related records.")
            return redirect('invoice_list')
        except Exception as e:
            logger.error(f"Error deleting invoice for user {request.user.id}: {e}")
            messages.error(self.request, "Error deleting invoice.")
            return redirect('invoice_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_page'] = 'invoices'
        return context
    

@login_required
def invoice_review(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)

    transactions = Transaction.objects.filter(
        invoice_numb=invoice.invoice_numb
    ).select_related('sub_cat', 'category')

    mileage_entries = Miles.objects.filter(
        invoice=invoice.invoice_numb,
        user=request.user,
        tax__iexact="Yes",
        mileage_type="Taxable"
    )
    try:
        rate = MileageRate.objects.first().rate if MileageRate.objects.exists() else Decimal('0.70')
        rate = Decimal(str(rate))
    except Exception as e:
        logger.error(f"Error fetching mileage rate: {e}")
        rate = Decimal('0.70')

    total_miles = mileage_entries.aggregate(Sum('total'))['total__sum'] or 0
    total_miles = Decimal(str(total_miles))
    mileage_dollars = (total_miles * rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    total_income = Decimal('0.00')
    total_expenses = Decimal('0.00')
    deductible_expenses = Decimal('0.00')

    for t in transactions:
        amount = Decimal(str(t.amount))

        if t.trans_type == 'Income':
            total_income += amount
        elif t.trans_type == 'Expense':
            total_expenses += amount
            is_meal = t.sub_cat and t.sub_cat.slug == 'meals'
            is_gas = t.sub_cat and t.sub_cat.slug == 'fuel'
            is_personal_vehicle = t.transport_type == 'personal_vehicle'

            if is_meal:
                deductible_expenses += Decimal(str(t.deductible_amount))
            elif is_gas and is_personal_vehicle:
                continue
            else:
                deductible_expenses += amount
        else:
            deductible_expenses += amount

    net_income = total_income - total_expenses
    taxable_income = total_income - deductible_expenses - mileage_dollars

    context = {
        'invoice': invoice,
        'transactions': transactions,
        'mileage_entries': mileage_entries,
        'mileage_dollars': mileage_dollars,
        'mileage_rate': rate,
        'total_expenses': total_expenses,
        'deductible_expenses': deductible_expenses,
        'total_income': total_income,
        'net_income': net_income,
        'taxable_income': taxable_income,
        'invoice_amount': invoice.amount,
        'current_page': 'invoices',
    }

    return render(request, 'finance/invoice_review.html', context)


@login_required
def invoice_review_pdf(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    transactions = Transaction.objects.filter(invoice_numb=invoice.invoice_numb).select_related('trans_type', 'sub_cat', 'category')
    mileage_entries = Miles.objects.filter(
        invoice=invoice.invoice_numb,
        user=request.user,
        tax__iexact="Yes",
        mileage_type="Taxable"
    )

    try:
        rate = MileageRate.objects.first().rate if MileageRate.objects.exists() else 0.70
    except Exception as e:
        logger.error(f"Error fetching mileage rate: {e}")
        rate = 0.70

    total_mileage_miles = mileage_entries.aggregate(Sum('total'))['total__sum'] or 0
    mileage_dollars = round(total_mileage_miles * rate, 2)

    total_expenses = 0
    deductible_expenses = 0
    total_income = 0

    for t in transactions:
        if t.trans_type.trans_type == 'Income':
            total_income += t.amount
        elif t.trans_type.trans_type == 'Expense':
            total_expenses += t.amount
            is_meal = t.sub_cat and t.sub_cat.id == 26
            is_gas = t.sub_cat and t.sub_cat.id == 27
            is_personal_vehicle = t.transport_type == 'personal_vehicle'

            if is_meal:
                deductible_expenses += t.deductible_amount
            elif is_gas and is_personal_vehicle:
                continue
            else:
                deductible_expenses += t.amount

    net_income = total_income - total_expenses
    taxable_income = total_income - deductible_expenses - mileage_dollars

    context = {
        'invoice': invoice,
        'transactions': transactions,
        'mileage_entries': mileage_entries,
        'mileage_rate': rate,
        'mileage_dollars': mileage_dollars,
        'invoice_amount': invoice.amount,
        'total_expenses': total_expenses,
        'deductible_expenses': deductible_expenses,
        'total_income': total_income,
        'net_income': net_income,
        'taxable_income': taxable_income,
        'now': now(),
        'current_page': 'invoices',
    }

    try:
        template = get_template('finance/invoice_review_pdf.html')
        html_string = template.render(context)
        html_string = "<style>@page { size: 8.5in 11in; margin: 1in; }</style>" + html_string

        if request.GET.get("preview") == "1":
            return HttpResponse(html_string)

        with tempfile.NamedTemporaryFile(delete=True) as tmp:
            HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf(tmp.name)
            tmp.seek(0)
            response = HttpResponse(tmp.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="invoice_{invoice.invoice_numb}.pdf"'
            return response
    except Exception as e:
        logger.error(f"Error generating PDF for invoice {pk} by user {request.user.id}: {e}")
        messages.error(request, "Error generating PDF.")
        return redirect('invoice_detail', pk=pk)
    
    
@login_required
def unpaid_invoices(request):
    invoices = Invoice.objects.filter(paid__iexact="No").select_related('client').order_by('due_date')
    context = {'invoices': invoices, 'current_page': 'invoices'}
    return render(request, 'components/unpaid_invoices.html', context)


@login_required
def export_invoices_csv(request):
    invoice_view = InvoiceListView()
    invoice_view.request = request
    queryset = invoice_view.get_queryset()

    class Echo:
        def write(self, value):
            return value

    def stream_csv(queryset):
        writer = csv.writer(Echo())
        yield writer.writerow(['Invoice #', 'Client', 'Location', 'Service', 'Amount', 'Date', 'Due', 'Paid', 'Days to Pay'])
        for invoice in queryset.iterator():
            yield writer.writerow([
                invoice.invoice_numb,
                str(invoice.client),
                str(invoice.service),
                invoice.amount,
                invoice.date,
                invoice.due,
                invoice.paid_date or "No",
                invoice.days_to_pay if invoice.paid_date else "—"
            ])

    try:
        response = StreamingHttpResponse(stream_csv(queryset), content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="invoices.csv"'
        return response
    except Exception as e:
        logger.error(f"Error generating CSV for user {request.user.id}: {e}")
        return HttpResponse("Error generating CSV", status=500)


@login_required
def export_invoices_pdf(request):
    invoice_view = InvoiceListView()
    invoice_view.request = request
    invoices = invoice_view.get_queryset()[:1000]

    if not invoices.exists():
        messages.error(request, "No invoices to export.")
        return redirect('invoice_list')

    try:
        template = get_template('finance/invoice_pdf_export.html')
        html_string = template.render({'invoices': invoices, 'current_page': 'invoices'})
        with tempfile.NamedTemporaryFile(delete=True) as output:
            HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf(output.name)
            output.seek(0)
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="invoices.pdf"'
            response.write(output.read())
            return response
    except Exception as e:
        logger.error(f"Error generating PDF for user {request.user.id}: {e}")
        messages.error(request, "Error generating PDF.")
        return redirect('invoice_list')
    

# ---------------------------------------------------------------------------------------------------------------  Categories


class CategoryListView(LoginRequiredMixin, ListView):
    model = Category
    template_name = 'finance/category_page.html'
    context_object_name = 'category'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sub_cat'] = SubCategory.objects.order_by('sub_cat')
        context['current_page'] = 'categories'
        return context


class CategoryCreateView(LoginRequiredMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = "components/category_form.html"
    success_url = reverse_lazy('category_page')

    def form_valid(self, form):
        messages.success(self.request, "Category added successfully!")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_page'] = 'categories'
        return context


class CategoryUpdateView(LoginRequiredMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = "components/category_form.html"
    success_url = reverse_lazy('category_page')

    def form_valid(self, form):
        messages.success(self.request, "Category updated successfully!")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_page'] = 'categories'
        return context


class CategoryDeleteView(LoginRequiredMixin, DeleteView):
    model = Category
    template_name = "components/category_confirm_delete.html"
    success_url = reverse_lazy('category_page')

    def delete(self, request, *args, **kwargs):
        try:
            response = super().delete(request, *args, **kwargs)
            messages.success(self.request, "Category deleted successfully!")
            return response
        except models.ProtectedError:
            messages.error(self.request, "Cannot delete category due to related transactions.")
            return redirect('category_page')
        except Exception as e:
            logger.error(f"Error deleting category for user {request.user.id}: {e}")
            messages.error(self.request, "Error deleting category.")
            return redirect('category_page')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_page'] = 'categories'
        return context


# ---------------------------------------------------------------------------------------------------------------   Sub-Categories


class SubCategoryCreateView(LoginRequiredMixin, CreateView):
    model = SubCategory
    form_class = SubCategoryForm
    template_name = "components/sub_category_form.html"
    success_url = reverse_lazy('category_page')

    def form_valid(self, form):
        messages.success(self.request, "Sub-Category added successfully!")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_page'] = 'categories'
        return context


class SubCategoryUpdateView(LoginRequiredMixin, UpdateView):
    model = SubCategory
    form_class = SubCategoryForm
    template_name = "components/sub_category_form.html"
    success_url = reverse_lazy('category_page')
    context_object_name = "sub_cat"

    def form_valid(self, form):
        messages.success(self.request, "Sub-Category updated successfully!")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_page'] = 'categories'
        return context


class SubCategoryDeleteView(LoginRequiredMixin, DeleteView):
    model = SubCategory
    template_name = "components/sub_category_confirm_delete.html"
    success_url = reverse_lazy('category_page')

    def delete(self, request, *args, **kwargs):
        try:
            response = super().delete(request, *args, **kwargs)
            messages.success(self.request, "Sub-Category deleted successfully!")
            return response
        except models.ProtectedError:
            messages.error(self.request, "Cannot delete sub-category due to related transactions.")
            return redirect('category_page')
        except Exception as e:
            logger.error(f"Error deleting sub-category for user {request.user.id}: {e}")
            messages.error(self.request, "Error deleting sub-category.")
            return redirect('category_page')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_page'] = 'categories'
        return context


# ---------------------------------------------------------------------------------------------------------------  Clients


class ClientListView(LoginRequiredMixin, ListView):
    model = Client
    template_name = "components/client_list.html"
    context_object_name = "clients"
    ordering = ['business']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_page'] = 'clients'
        return context


class ClientCreateView(LoginRequiredMixin, CreateView):
    model = Client
    form_class = ClientForm
    template_name = "components/client_form.html"
    success_url = reverse_lazy('client_list')

    def form_valid(self, form):
        messages.success(self.request, "Client added successfully!")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_page'] = 'clients'
        return context


class ClientUpdateView(LoginRequiredMixin, UpdateView):
    model = Client
    form_class = ClientForm
    template_name = "components/client_form.html"
    success_url = reverse_lazy('client_list')

    def form_valid(self, form):
        messages.success(self.request, "Client updated successfully!")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_page'] = 'clients'
        return context


class ClientDeleteView(LoginRequiredMixin, DeleteView):
    model = Client
    template_name = "components/client_confirm_delete.html"
    success_url = reverse_lazy('client_list')

    def delete(self, request, *args, **kwargs):
        try:
            response = super().delete(request, *args, **kwargs)
            messages.success(self.request, "Client deleted successfully!")
            return response
        except models.ProtectedError:
            messages.error(self.request, "Cannot delete client due to related invoices.")
            return redirect('client_list')
        except Exception as e:
            logger.error(f"Error deleting client for user {request.user.id}: {e}")
            messages.error(self.request, "Error deleting client.")
            return redirect('client_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_page'] = 'clients'
        return context


# --------------------------------------------------------------------------------------------------------------- Financial Reports


def get_summary_data(request, year):
    current_year = timezone.now().year

    try:
        if isinstance(year, int):
            selected_year = year
        elif isinstance(year, str) and year.strip().isdigit():
            selected_year = int(year)
        elif year in (None, '', 'All'):
            selected_year = current_year
        else:
            raise ValueError
    except ValueError:
        messages.error(request, "Invalid year selected.")
        selected_year = current_year

    expense_transactions = Transaction.objects.filter(
        user=request.user,
        date__year=selected_year,
        trans_type='Expense'
    ).select_related('sub_cat')

    expense_totals = {}
    for t in expense_transactions:
        name = t.sub_cat.sub_cat if t.sub_cat else "Uncategorized"

        if t.sub_cat_id == 27 and t.transport_type == "personal_vehicle":
            continue

        amount = t.amount
        if t.sub_cat_id == 26:
            amount = round(t.amount * Decimal('0.5'), 2)

        expense_totals[name] = expense_totals.get(name, Decimal('0.00')) + amount

    expense_subcategory_totals = [
        {'sub_cat__sub_cat': name, 'total': total}
        for name, total in sorted(expense_totals.items())
    ]

    income_qs = Transaction.objects.filter(
        user=request.user,
        date__year=selected_year,
        trans_type='Income'
    ).select_related('sub_cat', 'category')

    income_subcategory_totals = income_qs.values('sub_cat__sub_cat') \
        .annotate(total=Sum('amount')).order_by('sub_cat__sub_cat')

    income_category_totals = income_qs.values('category__category') \
        .annotate(total=Sum('amount')).order_by('category__category')

    expense_category_totals = Transaction.objects.filter(
        user=request.user,
        date__year=selected_year,
        trans_type='Expense'
    ).values('category__category') \
     .annotate(total=Sum('amount')).order_by('category__category')

    income_category_total = income_qs.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    expense_category_total = sum(t.get('total', Decimal('0.00')) for t in expense_subcategory_totals)
    net_profit = income_category_total - expense_category_total
    available_years = Transaction.objects.filter(user=request.user).dates('date', 'year', order='DESC')
    available_years = [d.year for d in available_years]

    return {
        'selected_year': selected_year,
        'income_subcategory_totals': income_subcategory_totals,
        'expense_subcategory_totals': expense_subcategory_totals,
        'income_category_totals': income_category_totals,
        'expense_category_totals': expense_category_totals,
        'income_category_total': income_category_total,
        'expense_category_total': expense_category_total,
        'expense_subcategory_total': sum(t.get('total', Decimal('0.00')) for t in expense_subcategory_totals),
        'net_profit': net_profit,
        'available_years': available_years,
    }



@login_required
def financial_statement(request):
    current_year = timezone.now().year
    year = request.GET.get('year', str(current_year))
    context = get_summary_data(request, year)
    context['available_years'] = [d.year for d in Transaction.objects.filter(
        user=request.user).dates('date', 'year', order='DESC').distinct()]
    context['current_page'] = 'reports'
    return render(request, 'finance/financial_statement.html', context)


@login_required
def financial_statement_pdf(request, year):
    user = request.user
    selected_year = int(year)

    transactions = Transaction.objects.filter(
        user=user,
        date__year=selected_year,
        trans_type='Expense'
    ).select_related('sub_cat')

    expense_totals = {}
    for t in transactions:
        name = t.sub_cat.sub_cat if t.sub_cat else "Uncategorized"
        if t.sub_cat_id == 27 and t.transport_type == "personal_vehicle":
            continue
        amount = t.amount
        if t.sub_cat_id == 26:
            amount = round(t.amount * Decimal('0.5'), 2)
        expense_totals[name] = expense_totals.get(name, Decimal('0.00')) + amount

    expense_subcategory_totals = [
        {'sub_cat__sub_cat': name, 'total': total}
        for name, total in sorted(expense_totals.items())
    ]
    expense_category_total = sum(t['total'] for t in expense_subcategory_totals)

    income_qs = Transaction.objects.filter(
        user=user,
        date__year=selected_year,
        trans_type='Income'
    ).select_related('sub_cat')

    income_subcategory_totals = income_qs.values('sub_cat__sub_cat') \
        .annotate(total=Sum('amount')).order_by('sub_cat__sub_cat')
    income_category_total = income_qs.aggregate(total=Sum('amount'))['total'] or 0

    net_profit = income_category_total - expense_category_total

    html_string = render_to_string('finance/financial_statement_pdf.html', {
        'selected_year': selected_year,
        'income_subcategory_totals': income_subcategory_totals,
        'expense_subcategory_totals': expense_subcategory_totals,
        'income_category_total': income_category_total,
        'expense_category_total': expense_category_total,
        'net_profit': net_profit,
        'now': timezone.now(),
    })
    pdf = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf()
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'filename="Financial_Statement_{selected_year}.pdf"'
    return response
    
    
@login_required
def category_summary(request):
    year = request.GET.get('year')
    context = get_summary_data(request, year)
    context['available_years'] = [d.year for d in Transaction.objects.filter(
        user=request.user).dates('date', 'year', order='DESC').distinct()]
    context['current_page'] = 'reports'
    return render(request, 'finance/category_summary.html', context)


@login_required
def category_summary_pdf(request):
    year = request.GET.get('year')
    context = get_summary_data(request, year)
    context['now'] = timezone.now()
    context['selected_year'] = year or timezone.now().year

    try:
        template = get_template('finance/category_summary_pdf.html')
        html_string = template.render(context)
        html_string = "<style>@page { size: 8.5in 11in; margin: 1in; }</style>" + html_string

        if request.GET.get("preview") == "1":
            return HttpResponse(html_string)

        with tempfile.NamedTemporaryFile(delete=True) as tmp:
            HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf(tmp.name)
            tmp.seek(0)
            response = HttpResponse(tmp.read(), content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="category_summary.pdf"'
            return response
    except Exception as e:
        logger.error(f"Error generating category summary PDF: {e}")
        messages.error(request, "Error generating PDF.")
        return redirect('category_summary')


@login_required
def reports_page(request):
    context = {'current_page': 'reports'}
    return render(request, 'finance/reports.html', context)


# ---------------------------------------------------------------------------------------------------------------   Emails

logger = logging.getLogger(__name__)

@require_POST
def send_invoice_email(request, invoice_id):
    invoice = get_object_or_404(Invoice, pk=invoice_id)
    try:
        # Generate invoice HTML and PDF
        html_string = render_to_string('finance/invoice_detail.html', {
            'invoice': invoice,
            'current_page': 'invoices'
        })
        html = HTML(string=html_string, base_url=request.build_absolute_uri())
        pdf_file = html.write_pdf()

        # Email content
        subject = f"Invoice #{invoice.invoice_numb} from Sky Guy"
        body = f"""
        Hi {invoice.client.first},<br><br>
        Attached is your invoice for the event: <strong>{invoice.event}</strong>.<br><br>
        Let me know if you have any questions!<br><br>
        Thank you!,<br>
        <strong>Anthony</strong><br>
        Sky Guy LLC<br>
        <a href="http://www.airborneimages.com" target="_blank">www.AirborneImages.com</a><br>
        "Photography with Altitude"<br>
        """

        from_email = "skyguyllc@gmail.com"
        recipient = [invoice.client.email or getattr(settings, 'DEFAULT_EMAIL', None)]
        if not recipient[0]:
            raise ValueError("No valid email address provided.")

        email = EmailMessage(
            subject=subject,
            body=body,
            from_email=from_email,
            to=recipient,
            bcc=["skyguyllc@gmail.com"]
        )
        email.content_subtype = 'html'
        email.attach(f"Invoice_{invoice.invoice_numb}.pdf", pdf_file, "application/pdf")
        email.send()

        return JsonResponse({'status': 'success', 'message': 'Invoice emailed successfully!'})
    except Exception as e:
        logger.error(f"Error sending email for invoice {invoice_id} by user {request.user.id}: {e}")
        return JsonResponse({'status': 'error', 'message': 'Failed to send email'}, status=500)



# ---------------------------------------------------------------------------------------------------------------  Mileage


def get_mileage_context(request):
    try:
        rate = MileageRate.objects.first().rate if MileageRate.objects.exists() else Decimal('0.70')
        rate = Decimal(str(rate))
    except Exception as e:
        logger.error(f"Error fetching mileage rate: {e}")
        rate = Decimal('0.70')
        messages.error(request, "Error fetching mileage rate. Using default rate.")

    except Exception as e:
        logger.error(f"Error fetching mileage rate: {e}")
        rate = 0.70
        messages.error(request, "Error fetching mileage rate. Using default rate.")

    year = datetime.now().year
    entries = Miles.objects.filter(user=request.user, date__year=year)
    paginator = Paginator(entries, 50)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    taxable = entries.filter(mileage_type='Taxable')
    total_miles = taxable.aggregate(Sum('total'))['total__sum'] or 0

    return {
        'mileage_list': page_obj,
        'page_obj': page_obj,
        'total_miles': total_miles,
        'taxable_dollars': Decimal(str(total_miles)) * rate,
        'current_year': year,
        'mileage_rate': rate,
        'current_page': 'mileage'
    }


@login_required
def mileage_log(request):
    context = get_mileage_context(request)
    return render(request, 'finance/mileage_log.html', context)


class MileageCreateView(LoginRequiredMixin, CreateView):
    model = Miles
    form_class = MileageForm
    template_name = 'finance/mileage_form.html'
    success_url = reverse_lazy('mileage_log')

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, "Mileage entry added successfully!")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_page'] = 'mileage'
        return context


class MileageUpdateView(LoginRequiredMixin, UpdateView):
    model = Miles
    form_class = MileageForm
    template_name = 'finance/mileage_form.html'
    success_url = reverse_lazy('mileage_log')

    def get_queryset(self):
        return Miles.objects.filter(user=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, "Mileage entry updated successfully!")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_page'] = 'mileage'
        return context


class MileageDeleteView(LoginRequiredMixin, DeleteView):
    model = Miles
    template_name = 'finance/mileage_confirm_delete.html'
    success_url = reverse_lazy('mileage_log')

    def get_queryset(self):
        return Miles.objects.filter(user=self.request.user)

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Mileage entry deleted successfully!")
        return super().delete(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_page'] = 'mileage'
        return context


@login_required
def update_mileage_rate(request):
    mileage_rate = MileageRate.objects.first() or MileageRate(rate=0.70)
    if request.method == 'POST':
        form = MileageRateForm(request.POST, instance=mileage_rate)
        if form.is_valid():
            form.save()
            messages.success(request, "Mileage rate updated successfully!")
            return redirect('mileage_log')
        else:
            messages.error(request, "Error updating mileage rate. Please check the form.")
    else:
        form = MileageRateForm(instance=mileage_rate)
    context = {'form': form, 'current_page': 'mileage'}
    return render(request, 'components/update_mileage_rate.html', context)


# ---------------------------------------------------------------------------------------------------------------   Services


@login_required
def service_list(request):
    services = Service.objects.all()
    return render(request, 'finance/service_list.html', {'services': services})

@login_required
def service_create(request):
    if request.method == 'POST':
        form = ServiceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Service added successfully.")
            return redirect('service_list')
    else:
        form = ServiceForm()
    return render(request, 'finance/service_form.html', {'form': form, 'title': 'Add Service'})

@login_required
def service_update(request, pk):
    service = get_object_or_404(Service, pk=pk)
    if request.method == 'POST':
        form = ServiceForm(request.POST, instance=service)
        if form.is_valid():
            form.save()
            messages.success(request, "Service updated successfully.")
            return redirect('service_list')
    else:
        form = ServiceForm(instance=service)
    return render(request, 'finance/service_form.html', {'form': form, 'title': 'Edit Service'})

@login_required
def service_delete(request, pk):
    service = get_object_or_404(Service, pk=pk)
    if request.method == 'POST':
        service.delete()
        messages.success(request, "Service deleted.")
        return redirect('service_list')
    return render(request, 'finance/service_confirm_delete.html', {'service': service})
