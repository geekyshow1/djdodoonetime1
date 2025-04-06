from django.views import View
from django.shortcuts import render, redirect
from .forms import RegistrationForm
from dodopayments import DodoPayments
from django.conf import settings
from .models import UserProfile

client = DodoPayments(
    base_url=settings.DODO_API_URL,
    bearer_token=settings.DODO_PAYMENTS_API_KEY
)

class RegisterView(View):
    template_name = 'registration/register.html'

    def get(self, request):
        form = RegistrationForm()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request):
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            
            customer = client.customers.create(
                email= user.email,
                name=user.first_name,
            )
            dodo_customer_id = customer.customer_id
            if dodo_customer_id:
                user.save()
                profile, created = UserProfile.objects.get_or_create(user = user)

                profile.dodo_customer_id = dodo_customer_id
                profile.save()

            return redirect('login')
        return render(request, self.template_name, {'form': form})
    
