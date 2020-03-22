#----------------------- Imports------------------------------------------
from Users.forms import UserForm,ProfileForm
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from .models import Profile
from django.shortcuts import render, redirect
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from .tokens import account_activation_token
from django.contrib.auth.models import User
from django.core.mail import EmailMessage
from .forms import UpdateUserForm, UpdateProfileForm
from django.contrib import messages

#------------------------------------------------------------------------
# views.functions
#-----------------------------------------------------------------------

def index(request):
    return render(request,'Users/index.html') #welcome user to website
#------------------------------------------------------------------------
@login_required
def special(request):
    return HttpResponse("You are logged in !")

#-------------------------------------------------------------------------

def users_register(request):
    registered = False
    if request.method == 'POST':
        user_form = UserForm(data=request.POST)
        profile_form = ProfileForm(data=request.POST)
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()
            user.set_password(user.password)
            #it should be false but for easy testing login after register 
            # i set it true to skip activation and login easly.
            user.is_active = True
            user.save()


            current_site = get_current_site(request)
            mail_subject = 'Activate your account.'
            message = render_to_string('Users/active_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': account_activation_token.make_token(user)
            })
            to_email = user_form.cleaned_data.get('email')
            email = EmailMessage(
                        mail_subject, message, to=[to_email]
            )
            email.send()
            profile = profile_form.save(commit=False)
            profile.user = user
            if 'profile_pic' in request.FILES:
                print('found it')
                profile.profile_pic = request.FILES['profile_pic']
            profile.save()
            registered = True
        else:
            print(user_form.errors,profile_form.errors)
    else:
        user_form = UserForm()
        profile_form = ProfileForm()
    return render(request,'Users/registration.html',
                          {'user_form':user_form,
                           'profile_form':profile_form,
                           'registered':registered})

#-----------------------------------------------------------------

def users_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        # try:
        #     me = User.objects.get(username=request.POST['username'])
        #     if me.password == request.POST['password']:
        #         request.session['username'] = me.id
        #         return HttpResponseRedirect('/you-are-logged-in/')
        # except User.DoesNotExist:
        #      return HttpResponse("Your username and password didn't match.")
        # to login with both email and password , i set email=username in the query
        user = authenticate(username=User.objects.get(email=username), password=password)
        if user:
            if user.is_active:
                login(request,user)
                return HttpResponseRedirect('/Users/index')
            else:
                return HttpResponse("Your account was inactive.")
        else:
            print("Someone tried to login and failed.")
            print("They used username: {} and password: {}".format(username,password))
            return HttpResponse("Invalid login details given")
    else:
        return render(request, 'Users/login.html', {})
#-------------------------------------------------------------------------------

def activate(request, uidb64, token):
    try:
        #uid = force_text(urlsafe_base64_decode(uidb64))
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)
        return HttpResponse('Thank you for your email confirmation. Now you can login your account.')
    else:
        return HttpResponse('Activation link is invalid!')

#--------------------------------------------------------------------------------------
@login_required()
def user_profile(request):
    if request.method == 'POST':
        user_form = UpdateUserForm(request.POST, instance=request.user)
        profile_form =UpdateProfileForm(request.POST,
                                        request.FILES,
                                        instance=request.user.profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request,"Your account has been updated!")
            return redirect('/profile')
    else :
        user_form = UpdateUserForm(instance=request.user)
        profile_form = UpdateProfileForm(instance=request.user.profile)
    context = {
        'user_form': user_form,
        'profile_form': profile_form
    }
    return render(request,'Users/profile.html',context)
#--------------------------------------------------------------------------------

def users_logout(request):
    try:
        del request.session['username']
    except KeyError:
        pass
    return render(request,'Users/logout.html')