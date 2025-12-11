from django import forms
from django.contrib import admin
from django.db import connection, transaction
from store.models import Product
from django.urls import path
from django.http import HttpResponseRedirect
from django.urls import reverse
from store.models import ShippingAddress
from admin_volt.utils import call_stored_procedure, generate_report, generate_report_with_chart
from django.http import HttpResponse





class ProductForm(forms.ModelForm):
    amount = forms.IntegerField(min_value=0, required=False)

    class Meta:
        model = Product
        fields = '__all__'

    def save(self, commit=True):
        product = super().save(commit=False)
        if self.cleaned_data['amount']:
            # Kết nối tới cơ sở dữ liệu Oracle
            cursor = connection.cursor()

            # Gọi thủ tục PL/SQL để cập nhật số lượng tồn kho
            def call_procedure():
                cursor.callproc('add_more_product_stock', [product.id, self.cleaned_data['amount']])

            transaction.on_commit(call_procedure)

            # Đóng kết nối
            #cursor.close()

        if commit:
            product.save()
        return product

class ProductAdmin(admin.ModelAdmin):
    form = ProductForm



class ShippingAddressAdmin(admin.ModelAdmin):
    change_list_template = "admin/shippingaddress_changelist.html"
    

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('download_report/', self.admin_site.admin_view(self.download_report), name='store_shippingaddress_download_report'),
        ]
        return custom_urls + urls

    def download_report(self, request):
        # Gọi stored procedure và tạo báo cáo
        results = call_stored_procedure()
        #wb = generate_report(results)
        wb = generate_report(results)
        
        # Tạo response để trả về file Excel
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename=shipping_addresses_report.xlsx'
        wb.save(response)
        return response
