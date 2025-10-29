from django.shortcuts import render

from .forms import UserForm


# Create your views here.
def registerUser(request):
    if request.method == 'POST':
        forms = UserForm(request.POST)
        if forms.is_valid():
            forms.save()
    else:
        forms = UserForm()
    context = {
        'form': forms
    }
    return render(request,'accounts/registerUser.html',context)