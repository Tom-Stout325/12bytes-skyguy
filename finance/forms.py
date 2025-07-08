from django import forms
from django.forms import inlineformset_factory
from .models import *


class TransactionsForm(forms.ModelForm):

    class Meta:
        model = Transaction
        fields = (
            'date', 'trans_type', 'sub_cat', 'amount',
            'invoice_numb', 'transaction',
            'receipt', 'transport_type'
        )
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'transport_type': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean_receipt(self):
        receipt = self.cleaned_data.get('receipt')
        if receipt and hasattr(receipt, 'content_type'):
            if receipt.content_type not in ['application/pdf', 'image/jpeg', 'image/png']:
                raise forms.ValidationError("Only PDF, JPG, or PNG files are allowed.")
        return receipt

    def clean(self):
        cleaned_data = super().clean()
        transport = cleaned_data.get("transport_type")
        sub_cat = cleaned_data.get("sub_cat")

        if transport == "personal_vehicle" and sub_cat and sub_cat.sub_cat.lower() in ['fuel', 'gas', 'gasoline']:
            raise forms.ValidationError(
                "Gas expenses are not deductible when using a personal vehicle. Use mileage instead."
            )

        if not sub_cat:
            raise forms.ValidationError("You must select a Sub-Category.")

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if instance.sub_cat:
            instance.category = instance.sub_cat.category 
        if commit:
            instance.save()
        return instance




class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = [
            'invoice_numb', 'client', 'event', 'location',
            'service', 'amount', 'date', 'due', 'paid_date', 'status'
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'due': forms.DateInput(attrs={'type': 'date'}),
            'paid_date': forms.DateInput(attrs={'type': 'date'}),
        }
    

class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['service']
        widgets = {
            'service': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter service name'}),
        }



class InvoiceItemForm(forms.ModelForm):
    class Meta:
        model = InvoiceItem
        fields = ['description', 'qty', 'price']

    description = forms.CharField(
        label="Description",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Service or product description'})
    )

    qty = forms.IntegerField(
        label="Qty",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 1})
    )

    price = forms.DecimalField(
        label="Price",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )



InvoiceItemFormSet = inlineformset_factory(
    Invoice,
    InvoiceItem,
    form=InvoiceItemForm,
    extra=5,
    can_delete=True
)
    

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['category']


class SubCategoryForm(forms.ModelForm):
    class Meta:
        model = SubCategory
        fields = ['sub_cat']


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['business', 'first', 'last', 'street', 'address2', 'email', 'phone']


class MileageForm(forms.ModelForm):
    class Meta:
        model = Miles
        exclude = ['user', 'total']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'begin': forms.NumberInput(attrs={'step': '0.1', 'class': 'form-control'}),
            'end': forms.NumberInput(attrs={'step': '0.1', 'class': 'form-control'}),
            'client': forms.Select(attrs={'class': 'form-control'}),
            'invoice': forms.TextInput(attrs={'class': 'form-control'}),
            'tax': forms.TextInput(attrs={'class': 'form-control'}),
            'job': forms.TextInput(attrs={'class': 'form-control'}),
            'vehicle': forms.TextInput(attrs={'class': 'form-control'}),
            'mileage_type': forms.Select(attrs={'class': 'form-control'}),
        }

class MileageRateForm(forms.ModelForm):
    class Meta:
        model = MileageRate
        fields = ['rate']
        widgets = {
            'rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

