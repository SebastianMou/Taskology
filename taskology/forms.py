from django import forms
from tinymce.widgets import TinyMCE
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Task

class UserRegisterForm(UserCreationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control form-group', 
        'placeholder': 'Username',
    }))
    email = forms.EmailField(required=True, widget=forms.TextInput(attrs={
        'class': 'form-control form-group', 
        'placeholder': 'Email'
    }))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control form-group',
        'placeholder': 'password',
    }))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control form-group',
        'placeholder': 'Confirm Password',
    }))

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class TaskForm(forms.ModelForm):
    title = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'underline-input',
        'placeholder': 'Task Title',
    }))
    completion_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'underline-input',
            'type': 'date',
            'placeholder': 'YYYY-MM-DD',
        })
    )
    completion_time = forms.TimeField(
        required=False,
        widget=forms.TimeInput(attrs={
            'class': 'underline-input',
            'type': 'time',
            'placeholder': 'HH:MM:SS',
        })
    )
    description = forms.CharField(widget=TinyMCE(attrs={'cols': 80, 'rows': 30}), required=False)

    class Meta:
        model = Task
        fields = ['title', 'completion_date', 'completion_time', 'description']