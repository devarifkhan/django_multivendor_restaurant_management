from django.shortcuts import render, redirect

from .forms import UserForm
from .models import User
from django.contrib import messages
# Create your views here.
def registerUser(request):
    if request.method == 'POST':
        forms = UserForm(request.POST)
        if forms.is_valid():
            # password = forms.cleaned_data['password']
            # user = forms.save(commit=False)
            # user.set_password(password)
            # user.role = User.CUSTOMER
            # forms.save()
            # create the user using create_user method
            first_name = forms.cleaned_data['first_name']
            last_name = forms.cleaned_data['last_name']
            username = forms.cleaned_data['username']
            email = forms.cleaned_data['email']
            password = forms.cleaned_data['password']
            user = User.objects.create_user(first_name=first_name, last_name=last_name, username=username, email=email, password=password)
            user.role = User.CUSTOMER
            user.save()
            messages.success(request, 'Your account has been registered successfully.')
            return redirect('registerUser')
    else:
        forms = UserForm()
    context = {
        'form': forms
    }
    return render(request,'accounts/registerUser.html',context)

def registerVendor(request):
    if request.method == 'POST':
        forms = UserForm(request.POST)
        if forms.is_valid():
            # password = forms.cleaned_data['password']
            # user = forms.save(commit=False)
            # user.set_password(password)
            # user.role = User.RESTAURANT
            # forms.save()
            # create the user using create_user method
            first_name = forms.cleaned_data['first_name']
            last_name = forms.cleaned_data['last_name']
            username = forms.cleaned_data['username']
            email = forms.cleaned_data['email']
            password = forms.cleaned_data['password']
            user = User.objects.create_user(first_name=first_name, last_name=last_name, username=username, email=email, password=password)
            user.role = User.RESTAURANT
            user.save()
            messages.success(request, 'Your account has been registered successfully.')
            return redirect('registerVendor')
    else:
        forms = UserForm()
    context = {
        'form': forms
    }
    return render(request, 'accounts/registerVendor.html', context)