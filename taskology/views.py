from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.models import User

from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage

from .tokens import account_activation_token
from .models import Task, CompanyNotification
from .forms import TaskForm, UserRegisterForm

# Create your views here.
@login_required
def home(request):
    all_tasks = Task.objects.order_by('position').filter(owner=request.user)
    task_count = all_tasks.count()
    status_counts = {status: all_tasks.filter(status=status).count() for status, _ in Task.STATUS_CHOICES}
    form_submitted = False  # Initialize the flag

    if request.method == 'POST':
        form_task = TaskForm(request.POST)
        if form_task.is_valid():
            task = form_task.save(commit=False)
            task.owner = request.user
            task.save()
            if request.headers.get('HX-Request', 'false').lower() == 'true':
                tasks = all_tasks
                # For HTMX requests, render the partial template without setting form_submitted to True
                return render(request, 'partials/_task_list.html', {'tasks': tasks})
            else:
                # For non-HTMX requests, redirect to 'home' which causes a full page reload
                return redirect('home')
        # If the form is not valid, fall through to render the page with the form errors
    else:
        form_task = TaskForm()

    context = {
        'tasks': all_tasks,
        'task_count': task_count,
        'status_counts': status_counts,
        'form_task': form_task,
        'form_submitted': form_submitted,  # This remains False for GET requests and invalid POST requests
    }
    return render(request, 'home.html', context)

def update_task_order(request):
    """
    Handle the request to update the order and status of tasks.

    This view expects a POST request with 'item' and 'status' data.
    'item' contains the IDs of tasks in their current order.
    'status' contains the status of each task.

    The function updates the position and status of each task in the database.
    """
    # Check if the request method is POST.
    if request.method == "POST":
        
        # Extract the list of task IDs from the POST data.
        items = request.POST.getlist('item')
        
        # Extract the list of statuses from the POST data.
        statuses = request.POST.getlist('status')
        
        # Print the received items and statuses for debugging purposes.
        print("Received items:", items)  
        print("Received statuses:", statuses) 
        
        # Loop through each task ID and status.
        for index, (item_id, status) in enumerate(zip(items, statuses)):
            
            # Fetch the task object from the database using its ID.
            task = Task.objects.get(id=item_id)
            
            # Update the task's position based on its order in the received list.
            task.position = index
            
            # Update the task's status.
            task.status = status
            
            # Save the updated task to the database.
            task.save()

    # Return a 204 No Content response to indicate successful processing.
    return HttpResponse(status=204)

def items_detail(request, pk):
    task = get_object_or_404(Task, id=pk)
    context = {
        'task': task,
    }
    return render(request, 'task/items_detail.html', context)

@login_required
def delete_task(request, pk):
    task = get_object_or_404(Task, id=pk, owner=request.user)  # Ensure the task belongs to the logged-in user
    if request.method == 'POST':  # Confirm the task deletion with a POST request
        task.delete()
        return redirect('home')  # Redirect to the tasks view after deletion
    context = {
        'task': task,
    }
    return render(request, 'task/confirm_delete.html', context)

@login_required
def edit_task(request, pk):
    task = get_object_or_404(Task, id=pk, owner=request.user)  # Ensure the task belongs to the logged-in user
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            return redirect('home')  
    else:
        form = TaskForm(instance=task) 
    context = {
        'form': form,
        'task': task,
    }
    return render(request, 'task/edit_task.html', context)

def all_notifications(request):
    notify = CompanyNotification.objects.all()
    context = {
        'notify': notify,
    }
    return render(request, 'company/notification.html', context)

def notification_detail(request, pk):
    notification = get_object_or_404(CompanyNotification, pk=pk)
    return render(request, 'company/notification_detail.html', {'notification': notification})

def user_login(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('/')
        else:
            messages.success(request, "Invalid username or password.")

    return render(request, 'authentication/user_login.html')

def login_with_email(request):
    if request.method == 'POST':
        email = request.POST["email"]
        password = request.POST["password"]
        try:
            user_obj = User.objects.get(email=email)
            user = authenticate(request, username=user_obj.username, password=password)
        except User.DoesNotExist:
            user = None

        if user is not None:
            login(request, user)
            return redirect('/')
        else:
            messages.error(request, "Invalid email or password.")
    return render(request, 'authentication/login_with_email.html')

def user_logout(request):
    logout(request)
    return HttpResponseRedirect(reverse('user_login'))

def user_register(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse('home'))
    else:
        if request.method == 'POST':
            form = UserRegisterForm(request.POST)
            if form.is_valid():
                email = form.cleaned_data.get('email')
                username = form.cleaned_data.get('username')
                if User.objects.filter(email=email) and User.objects.filter(username=username).exists():
                    messages.error(request, 'This email is already registered.')
                    return redirect('user_register')
                else:
                    user = form.save(commit=False)
                    user.is_active = False
                    user.save()
                    activateEmail(request, user, form.cleaned_data.get('email'))
                    return redirect('sending_activate_token')
        else:
            form = UserRegisterForm()
        context = {
            'form': form,
        }
        return render(request, 'authentication/register.html', context)

def activate(request, uidb64, token):
    User = get_user_model()
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()

        messages.success(request, 'Thank you for confirming your email. Please login USERNAME first time in to your account.')
        return redirect('user_login')
    else:
        messages.error(request, 'The activation link is not valid!')
    
    return render(request, 'authentication/user_login.html')

def activateEmail(request, user, to_email):
    mail_subject = 'Activate your user account.'
    message = render_to_string('authentication/template_activate_account.html', {
        'user': user.username,
        'domain': get_current_site(request).domain.split('://')[-1],  # This ensures only the domain is taken
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': account_activation_token.make_token(user),
        'protocol': 'https' if request.is_secure() else 'http'
    })
    email = EmailMessage(mail_subject, message, to=[to_email])
    email.content_subtype = "html"  
    if email.send():
        messages.success(request, f'Dear {user}, please go to your email {to_email} and click on the activation link you received to confirm and complete the registration. Note: Check your spam folder.')
    else:
        messages.error(request, f'Problem sending confirmation email to {to_email}, please check if you entered it correctly.')

def sending_activate_token(request):
    return render(request, 'authentication/sending_activate_token.html')

def public_privacy_policy(request):
    return render(request, 'legal/public_privacy_policy.html')

def public_terms_of_service(request):
    return render(request, 'legal/public_terms_of_service.html')

def all_tasks(request):
    all_tasks = Task.objects.filter(owner=request.user)
    if request.method == 'POST':
        form_task = TaskForm(request.POST)
        if form_task.is_valid():
            task = form_task.save(commit=False)
            task.owner = request.user
            task.save()
            if "HX-Request" in request.headers:
                # This is an HTMX request; return updated tasks list
                html = render_to_string('task_checklist/_tasks_list.html', {'all_tasks': Task.objects.filter(owner=request.user)}, request=request)
                return HttpResponse(html)
            else:
                # For non-HTMX requests, redirect as usual
                return redirect('all_tasks')
    else:
        form_task = TaskForm()
    
    context = {
        'all_tasks': all_tasks,
        'form_task': form_task,
    }
    return render(request, 'task_checklist/all_tasks.html', context)

@login_required
def delete_task_ck(request, pk):
    task = get_object_or_404(Task, id=pk, owner=request.user)
    if request.method == 'POST':
        task.delete()
        return redirect('all_tasks')
    context = {
        'task': task,
    }
    return render(request, 'task/confirm_delete.html', context)
    
@login_required
def edit_task_ck(request, pk):
    task = get_object_or_404(Task, id=pk, owner=request.user)
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            return redirect('all_tasks') 
    else:
        form = TaskForm(instance=task) 
    
    context = {
        'form': form,
        'task': task,
    }
    return render(request, 'task/edit_task.html', context)