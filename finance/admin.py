from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *



    
class TransactionAdmin(admin.ModelAdmin):
    list_display    = ['date', 'sub_cat', 'amount', 'invoice_numb']


class GroupAdmin(admin.ModelAdmin):
    list_display    = ['name', 'date']
    

    
@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_numb', 'client', 'amount', 'status', 'paid_date', 'days_to_pay')

    def days_to_pay(self, obj):
        return obj.days_to_pay if obj.days_to_pay is not None else "-"
    days_to_pay.short_description = "Days to Pay"


class CategoryAdmin(admin.ModelAdmin):
    list_display = ['category', 'id']
    ordering = ['category']

class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'sub_cat', 'category', 'slug']
    readonly_fields = ['slug']



admin.site.register(InvoiceItem)
admin.site.register(MileageRate)
admin.site.register(Client)
admin.site.register(Service)
admin.site.register(Category, CategoryAdmin)
admin.site.register(SubCategory, SubCategoryAdmin)
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(Miles)