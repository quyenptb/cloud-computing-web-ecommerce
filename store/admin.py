from django.contrib import admin
from .models import *
from admin_volt.models import *


admin.site.register(Customer)
admin.site.register(Product, ProductAdmin)
admin.site.register(Order)
admin.site.register(OrderItem)
#admin.site.register(ShippingAddress)
admin.site.register(Post)
admin.site.register(Comment)
admin.site.register(ShippingAddress, ShippingAddressAdmin)






