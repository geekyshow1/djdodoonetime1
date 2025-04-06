from django.contrib import admin
from .models import Product, Order

class OrderAdmin(admin.ModelAdmin):
  list_display = ['id', 'user', 'product', 'dodo_payment_id', 'is_paid']

admin.site.register(Product)
admin.site.register(Order, OrderAdmin)
