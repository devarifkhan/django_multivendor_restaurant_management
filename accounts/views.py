from django.shortcuts import render, redirect

from .forms import UserForm


# Create your views here.
def registerUser(request):
    if request.method == 'POST':
        forms = UserForm(request.POST)
        if forms.is_valid():
            user = forms.save(commit=False)
            user.role = User.CUSTOMER
            forms.save()
            return redirect('registerUser')
    else:
        forms = UserForm()
    context = {
        'form': forms
    }
    return render(request,'accounts/registerUser.html',context)