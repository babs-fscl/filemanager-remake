from django.shortcuts import render, redirect, HttpResponse
from .models import CustomUser
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from .forms import UserRegisterForm, UserEditForm
from django.contrib.auth.decorators import login_required


def login_user(request):
    if request.user.is_authenticated:
        return redirect('upload')
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        credential = authenticate(request, username=email, password=password)
        previous_url = request.GET.get('next')
        if credential is not None:
            login(request, credential)
            if previous_url:
                return redirect(previous_url)
            else:
                return redirect('upload')
        else:
            messages.error(request, 'Invalid Username/Password')
            return redirect('login')
    else:
        return render(request, 'login.html', {})


def logout_user(request):
    logout(request)
    messages.success(request, 'You have logged out successfully.')
    return redirect('login')


def register_user(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user_cred = form.save(commit=False)
            
            # Create organization from company_name
            company_name = form.cleaned_data.get('company_name')
            from .models import Organization
            org, created = Organization.objects.get_or_create(name=company_name)
            
            user_cred.organization = org
            if created:
                user_cred.role = 'admin'
            else:
                user_cred.role = 'member'
            user_cred.save()
            
            login(request, user_cred, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('upload')

    else:
        form = UserRegisterForm()
    context = {'form': form}
    return render(request, 'signUp.html', context)


@login_required()
def organization_members(request):
    if request.user.role != 'admin':
        messages.error(request, "You do not have permission to view this page.")
        return redirect('upload')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password = request.POST.get('password')
        
        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, f"User with email {email} already exists.")
        else:
            try:
                # Provide defaults for required profile fields
                new_user = CustomUser.objects.create_user(
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    organization=request.user.organization,
                    role='member',
                    company_name=request.user.organization.name,
                    personal_telephone="N/A",
                    office_telephone="N/A",
                    address="N/A"
                )
                messages.success(request, f"Member {first_name} {last_name} added successfully.")
            except Exception as e:
                messages.error(request, f"Error adding member: {str(e)}")
        return redirect('organization_members')
        
    members = CustomUser.objects.filter(organization=request.user.organization)
    return render(request, 'organization_members.html', {'members': members})


@login_required
def selectionPage(request):
    return render(request, 'selectionPage.html', {})


#   @login_required()
#   def change_password(request):
#       if request.method == 'POST':
#           form = PasswordChangeForm(data=request.POST, user=request.user)
#           if form.is_valid():
#               form.save()
#               update_session_auth_hash(request, form.user)
#               messages.success(request, 'Password changed successfully')
#               return redirect('dashboard')

#           else:
#               form = PasswordChangeForm(user=request.user)
#           context = {'form': form}
#           return render(request, 'change_password.html', context)
