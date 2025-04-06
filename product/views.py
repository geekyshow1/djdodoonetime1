from django.shortcuts import render, redirect, get_object_or_404
from .forms import ProductForm
from django.views import View
from dodopayments import DodoPayments
from django.conf import settings
from product.models import Product, Order
import pycountry
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from standardwebhooks.webhooks import Webhook
from django.http import HttpResponse, JsonResponse

client = DodoPayments(
    base_url=settings.DODO_API_URL,
    bearer_token=settings.DODO_PAYMENTS_API_KEY
)

class ProductCreateView(View):
    template_name = 'product/create_product.html'

    def get(self, request):
        form = ProductForm()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request):
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save(commit=False)
            product.user = request.user

            product_dodo = client.products.create(
                name = product.name,
                price={
                    "currency": "USD",
                    "discount": 0,
                    "price": product.price * 100,
                    "purchasing_power_parity": False,
                    "type": "one_time_price",
                },
                tax_category="digital_products",
            )

            if product_dodo.product_id:
                product.dodo_product_id = product_dodo.product_id
                product.save()
            return redirect('home')
        
        return render(request, self.template_name, {'form': form})

    
class CheckoutView(View):
    def get(self, request, product_id):
        product = Product.objects.get(id=product_id)

        countries = [ ]
        country_codes = client.misc.list_supported_countries()
        for code in country_codes:
            country = pycountry.countries.get(alpha_2=code)
            if country:
                countries.append({'code':code, 'name':country.name})
        countries.sort(key=lambda x: x['name'])
        return render(request, 'product/checkout.html', {'product':product, 'countries': countries})
    
@method_decorator(csrf_exempt, name='dispatch')
class InitiatePaymentView(LoginRequiredMixin, View):
    def post(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)
        user_profile = request.user.userprofile
        dodo_customer_id = user_profile.dodo_customer_id

        billing = {
            "city": request.POST.get("city"),
            "country": request.POST.get("country"),
            "state": request.POST.get("state"),
            "street": request.POST.get("street"),
            "zipcode": request.POST.get("zipcode"),
        }

        payment = client.payments.create(
            billing=billing,
            customer={
                "customer_id": dodo_customer_id
            },
            product_cart=[{
                "product_id": product.dodo_product_id,
                "quantity": 1,
            }],
            payment_link=True,
            return_url= request.build_absolute_uri('/product/payment/success/')
        )

        Order.objects.create(
            user = request.user,
            product = product,
            dodo_payment_id = payment.payment_id
        )

        return redirect(payment.payment_link)
    
class PaymentResView(View):
    def get(self, request):
        return render(request, 'product/res.html')
    
@method_decorator(csrf_exempt, name='dispatch')
class DodoWebhookView(View):
    def post(self, request):
        try:
            # wh = Webhook(settings.DODO_WEBHOOK_SECRET)
            wh = Webhook("whsec_GRkQSq0VgT9Q7g6bR2fcZbcm")
            webhook_payload = request.body
            webhook_headers = request.headers
            event = wh.verify(webhook_payload, webhook_headers)
            print(f'Event114: {event}')

            event_type = event.get("type")
            data = event.get("data", {})

            payment_id = data.get("payment_id")
            status = data.get("status")

            if event_type == "payment.succeeded" and status == "succeeded":
                order = Order.objects.filter(dodo_payment_id=payment_id).first()
                if order:
                    order.is_paid = True
                    order.save()
                    return JsonResponse({"message": "Payment marked as paid."}, status=200)
                else:
                    return JsonResponse({"error": "Order not found."}, status=404)
                
            return JsonResponse({"message": "Event ignored."}, status=200)

        except Exception as e:
            print("Webhook error", str(e))
            return JsonResponse({"message": "failed."}, status=400)
