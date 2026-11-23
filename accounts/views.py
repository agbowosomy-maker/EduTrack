from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .forms import StudentRegistrationForm, UserLoginForm

# Create your views here.
def register(request):
    if request.user.is_authenticated:
        return redirect('accounts:role_redirect')
    if request.method=='POST':
        form=StudentRegistrationForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, 'Your student account has been created successfully. Please log in')
            return redirect('accounts:login')
    else:
        form=StudentRegistrationForm()

    return render(request, 'accounts/register.html', {'form':form})

def user_login(request):
    if request.user.is_authenticated:
        return redirect('accounts:role_redirect')
    if request.method=='POST':
        form=UserLoginForm(request, data=request.POST)

        if form.is_valid():
            user=form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name or user.username}!')
            return redirect('accounts:role_redirect') 
    else:
        form=UserLoginForm()

    return render(request,'accounts/login.html', {'form': form}) 

@login_required
def role_redirect(request):
    if request.user.role==request.user.Role.STUDENT:
        return redirect('dashboard:student_dashboard')
    elif request.user.role==request.user.Role.TEACHER:
        return redirect('dashboard:teacher_dashboard')
    
    return redirect('accounts:login')

@login_required
@require_POST
def user_logout(request):
    logout(request)
    messages.success(request, 'You have successfully logged out')

    return redirect('accounts:login')