from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Q

from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.views.decorators.http import require_http_methods

from .tokens import account_activation_token
from .models import Task, CompanyNotification, SubTask, TaskCategory
from .forms import TaskForm, UserRegisterForm, SubTaskForm, TaskCategoryForm

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
    sub_tasks = task.subtasks.all()
    context = {
        'task': task,
        'sub_tasks': sub_tasks,
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
def delete_all_tasks(request, category_id):
    if request.method == 'POST':
        tasks = Task.objects.filter(owner=request.user, category_id=category_id)
        tasks.delete()
        return redirect('category_detail', pk=category_id)
    else:
        return redirect('category_detail', pk=category_id)

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

def search(request):
    if request.method == 'POST':
        searched = request.POST.get('searched', '')
        task_categories = TaskCategory.objects.filter(name__icontains=searched)
        tasks = Task.objects.filter(
            Q(title__icontains=searched) |
            Q(completion_date__icontains=searched)
        )
        return render(request, 'company/search.html', {
            'searched': searched,
            'task_categories': task_categories,
            'tasks': tasks,
        })
    else:
        return render(request, 'company/search.html', {})

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

@login_required
def dashboard(request):
    task_categories_file = TaskCategory.objects.filter(owner=request.user)
    context = {
        'task_categories_file': task_categories_file,
    }
    return render(request, 'authentication/dashboard.html', context)

@login_required
def profile(request):
    task_categories_file = TaskCategory.objects.filter(owner=request.user)
    

    context = {
        'task_categories_file': task_categories_file,
    }
    return render(request, 'authentication/profile.html', context)

@login_required
def create_task_category(request):
    if request.method == 'POST':
        name = request.POST.get('name', None)
        owner = request.user  # This assumes the user is logged in

        if name:
            obj = TaskCategory.objects.create(name=name, owner=owner)
            data = {
                'id': obj.id,
                'name': obj.name,
            }
            return JsonResponse({'task_category': data}, status=200)
        else:
            return JsonResponse({'error': 'Name is required'}, status=400)

    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def category_detail(request, pk):
    task_category = get_object_or_404(TaskCategory, id=pk, owner=request.user)
    tasks = task_category.tasks.all()

    if request.method == 'POST':
        form_task = TaskForm(request.POST)
        if form_task.is_valid():
            task = form_task.save(commit=False)
            task.owner = request.user
            task.category = task_category
            task.save()

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                tasks_html = render_to_string('task_checklist/_tasks_list.html', {'tasks': task_category.tasks.all()}, request=request)
                return HttpResponse(tasks_html)
            else:
                return redirect('category_detail', pk=task_category.id)
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return HttpResponse("Form is not valid", status=400)
    
    else:
        form_task = TaskForm()

    context = {
        'task_category': task_category,
        'tasks': tasks,
        'form_task': form_task,
    }
    return render(request, 'task_checklist/category_detail.html', context)

@login_required
def create_subtask(request, task_id):
    task = get_object_or_404(Task, id=task_id, owner=request.user)

    if request.method == 'POST':
        sub_form = SubTaskForm(request.POST)
        if sub_form.is_valid():
            subtask = sub_form.save(commit=False)
            subtask.task = task
            subtask.save()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'message': 'SubTask created successfully!',
                    'subtask': {
                        'id': subtask.id,
                        'title': subtask.title,
                        'description': subtask.description,
                        'is_complete': subtask.is_complete,
                        'task_id': task.id
                    }
                }, status=200)
            return redirect('category_detail', pk=task.category.id)
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': 'Form submission error: ' + str(sub_form.errors)}, status=400)
            # Handle non-AJAX form errors here, if necessary
    return JsonResponse({'error': 'Invalid request method.'}, status=400)

@login_required
def category_delete(request, category_id):
    # Get the category, ensuring it belongs to the logged-in user
    category = get_object_or_404(TaskCategory, id=category_id, owner=request.user)

    if request.method == 'POST':
        category.delete()
        return redirect('profile')  # Redirect to a URL where you list categories or to the homepage, etc.
    else:
        return redirect('profile')

@login_required
def update_task_category(request, pk):
    # Fetch the instance; redirect if not found
    task_category = get_object_or_404(TaskCategory, id=pk, owner=request.user)

    if request.method == "POST":
        form = TaskCategoryForm(request.POST, instance=task_category)
        if form.is_valid():
            form.save()
            return redirect('profile')  # Redirect to a success page or the detail view
    else:
        form = TaskCategoryForm(instance=task_category)  # Load form to edit existing instance

    context = {
        'form': form,
    }
    return render(request, 'task_checklist/update_task_category.html', context)

def subtask_detail(request, pk):
    subtask = get_object_or_404(SubTask, id=pk)
    context = {
        'subtask': subtask, 
    }
    return render(request, 'task_checklist/subtask_detail.html', context)

@require_POST
def toggle_subtask_status(request):
    subtask_id = request.GET.get('subtask_id')
    subtask = get_object_or_404(SubTask, id=subtask_id)
    subtask.is_complete = not subtask.is_complete
    subtask.save()

    return JsonResponse({'title': subtask.title, 'is_complete': subtask.is_complete})

@login_required
@require_POST
def complete_task(request, task_id):
    task = get_object_or_404(Task, pk=task_id, owner=request.user)
    if task.status == 'COMPLETED':
        task.status = 'NOT_STARTED'
    else:
        task.status = 'COMPLETED'
    task.save()
    return JsonResponse({'status': task.status, 'task_id': task_id})

@login_required
def delete_task_ck(request, pk):
    task = Task.objects.get(id=pk, owner=request.user)
    task.delete()
    return redirect('category_detail', pk=task.category.pk)

@login_required
def edit_task_ck(request, pk):
    task = get_object_or_404(Task, id=pk, owner=request.user)
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            return redirect('category_detail', pk=task.category.pk) 
    else:
        form = TaskForm(instance=task) 
    
    context = {
        'form': form,
        'task': task,
    }
    return render(request, 'task/edit_task.html', context)