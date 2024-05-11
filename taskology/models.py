from django.db import models
from django.contrib.auth.models import User
from tinymce.models import HTMLField

# Create your models here.
class Task(models.Model):
    STATUS_CHOICES = [
        ('NOT_STARTED', 'Not Started'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
    ]
    title = models.CharField(max_length=255)
    completion_date = models.DateField(null=True, blank=True)  # Separate date field
    completion_time = models.TimeField(null=True, blank=True)  # Separate time field
    description = HTMLField(blank=True, null=True)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='NOT_STARTED')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    position = models.PositiveIntegerField(default=0, blank=False, null=False)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')

    def __str__(self) -> str:
        return str(self.title) + ' - ' + str(self.owner) + ' - ' + str(self.created_at)

    class Meta:
        verbose_name_plural = 'tasks'

class SubTask(models.Model):
    # A reference to the parent task
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='subtasks')
    
    # Basic subtask fields
    title = models.CharField(max_length=255)
    description = HTMLField(blank=True, null=True)
    is_complete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self) -> str:
        return f"{self.title} - {self.task.title} - Complete: {'Yes' if self.is_complete else 'No'}"

    class Meta:
        verbose_name_plural = 'subtasks'

class CompanyNotification(models.Model):
    title = models.CharField(max_length=255)
    description = HTMLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return str(self.title) + ' - ' + str(self.created_at)