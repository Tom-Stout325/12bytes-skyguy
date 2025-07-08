from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth.models import User
from datetime import timedelta, date
from decimal import Decimal
from django.conf import settings
from decimal import Decimal
from django.utils.text import slugify
try:
    from django.contrib.postgres.indexes import GinIndex
    from django.contrib.postgres.search import SearchVectorField
except ImportError:
    GinIndex = None
    SearchVectorField = None


class Category(models.Model):
    category = models.CharField(max_length=500, blank=True, null=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.category or "Unnamed Category"



class SubCategory(models.Model):
    sub_cat = models.CharField(max_length=500, blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subcategories')
    slug = models.SlugField(max_length=100, unique=True, blank=True)


    class Meta:
        verbose_name_plural = "Sub Categories"
        ordering = ['sub_cat']

    def __str__(self):
        return f"{self.category} - {self.sub_cat or 'Unnamed SubCategory'}"

    def save(self, *args, **kwargs):
        if not self.slug and self.sub_cat:
            self.slug = slugify(self.sub_cat)
        super().save(*args, **kwargs)




class Client(models.Model):
    business  = models.CharField(max_length=500, blank=True, null=True)
    first     = models.CharField(max_length=500, blank=True, null=True)
    last      = models.CharField(max_length=500, blank=True, null=True)
    street    = models.CharField(max_length=500, blank=True, null=True)
    address2  = models.CharField(max_length=500, blank=True, null=True)
    email     = models.EmailField(max_length=254)
    phone     = models.CharField(max_length=500, blank=True, null=True)
    
    def __str__(self):
        return self.business
    
    
class Service(models.Model):
    service = models.CharField(max_length=500, blank=True, null=True) 
    
    def __str__(self):
        return self.service
    
    
    
class Transaction(models.Model):
    TRANSPORT_CHOICES = [
        ('personal_vehicle', 'Personal Vehicle'),
        ('rental_car', 'Rental Car'),
        ('flight', 'Flight'),
        ('public_transport', 'Public Transport'),
    ]
    INCOME = 'Income'
    EXPENSE = 'Expense'

    TRANS_TYPE_CHOICES = [
        (INCOME, 'Income'),
        (EXPENSE, 'Expense'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    trans_type = models.CharField(max_length=10, choices=TRANS_TYPE_CHOICES, default=EXPENSE)
    category = models.ForeignKey('Category', on_delete=models.PROTECT)
    sub_cat = models.ForeignKey('SubCategory', on_delete=models.PROTECT, null=True, blank=True)
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    transaction = models.CharField(max_length=255)
    tax = models.CharField(max_length=10, default="Yes")
    receipt = models.FileField(upload_to='receipts/', blank=True, null=True)
    account = models.CharField(max_length=255, blank=True, null=True)
    date = models.DateField()
    invoice_numb = models.CharField(max_length=255, blank=True, null=True)
    transport_type = models.CharField(max_length=30, choices=TRANSPORT_CHOICES, null=True, blank=True, help_text="Used to identify if actual expenses apply")

    class Meta:
        indexes = [
            models.Index(fields=['date', 'trans_type']),
            models.Index(fields=['user', 'date']),
            models.Index(fields=['category']),
            models.Index(fields=['sub_cat']),
            models.Index(fields=['invoice_numb']),
        ]
        verbose_name_plural = "Transactions"
        ordering = ['date']
        
    @property
    def deductible_amount(self):
        if self.sub_cat_id == 26:
            return round(self.amount * Decimal('0.5'), 2)
        return self.amount

    def __str__(self):
        return f"{self.transaction} - {self.amount}"
    


class Invoice(models.Model):
    invoice_numb = models.CharField(max_length=10, unique=True)
    client = models.ForeignKey('Client', on_delete=models.PROTECT)
    event = models.CharField(max_length=500, blank=True, null=True)
    location = models.CharField(max_length=500, blank=True, null=True)
    service = models.ForeignKey('Service', on_delete=models.PROTECT)
    amount = models.DecimalField(default=0.00, max_digits=12, decimal_places=2)
    date = models.DateField() 
    due = models.DateField()
    paid_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[('Unpaid', 'Unpaid'), ('Paid', 'Paid'), ('Partial', 'Partial')],
        default='Unpaid'
    )
    search_vector = SearchVectorField(null=True, blank=True) if SearchVectorField else None

    class Meta:
        indexes = [
            models.Index(fields=['invoice_numb']),
            models.Index(fields=['date']),
            models.Index(fields=['due']),
            models.Index(fields=['paid_date']),
            models.Index(fields=['client']),
            models.Index(fields=['service']),
        ]
        if GinIndex and 'django.contrib.postgres' in settings.INSTALLED_APPS:
            indexes.append(
                GinIndex(fields=['search_vector'], name='invoice_search_idx')
            )
        ordering = ['invoice_numb']

    def __str__(self):
        return self.invoice_numb

    def calculate_total(self):
        return sum(item.total for item in self.items.all())

    @property
    def is_paid(self):
        return self.paid_date is not None

    @property
    def days_to_pay(self):
        if self.paid_date:
            return (self.paid_date - self.date).days
        return None


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    description = models.CharField(max_length=255)
    qty = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.description



class MileageRate(models.Model):
    rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.70)
    
    def __str__(self):
        return f"Current Mileage Rate: ${self.rate}"

    class Meta:
        verbose_name = "Mileage Rate"
        verbose_name_plural = "Mileage Rates"



class Miles(models.Model):
    MILEAGE_TYPE_CHOICES = [
        ('Taxable', 'Taxable'),
        ('Reimbursed', 'Reimbursed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    begin = models.DecimalField(max_digits=10, decimal_places=1, null=True, validators=[MinValueValidator(0)])
    end = models.DecimalField(max_digits=10, decimal_places=1, null=True, validators=[MinValueValidator(0)])
    total = models.DecimalField(max_digits=10, decimal_places=1, null=True, editable=False)
    client = models.ForeignKey('Client', on_delete=models.PROTECT)
    invoice = models.CharField(max_length=255, blank=True, null=True)
    tax = models.CharField(max_length=10, blank=False, null=True, default="Yes")
    job = models.CharField(max_length=255, blank=True, null=True)
    vehicle = models.CharField(max_length=255, blank=False, null=True, default="Lead Foot")
    mileage_type = models.CharField(max_length=20, choices=MILEAGE_TYPE_CHOICES, default='Taxable')

    class Meta:
        indexes = [
            models.Index(fields=['user', 'date']),
            models.Index(fields=['mileage_type']),
        ]
        verbose_name_plural = "Miles"
        ordering = ['-date']

    def __str__(self):
        return f"{self.date} - {self.client}"

    def save(self, *args, **kwargs):
        if self.begin is not None and self.end is not None:
            self.total = round(self.end - self.begin, 1)
        else:
            self.total = None
        super().save(*args, **kwargs)

