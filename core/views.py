from django.shortcuts import render
from django.views import View

from product.models import Product

# Create your views here.
class HomeView(View):
    def get(self, request):
        products = Product.objects.all()
        return render(request, 'core/home.html', {'products': products})