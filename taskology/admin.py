from django.contrib import admin
from .models import Task, CompanyNotification, SubTask

# Register your models here.
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'completion_time', 'owner', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at', 'updated_at', 'completion_time')
    search_fields = ('title', 'description', 'owner__username')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'status', 'completion_time', 'position', 'owner')
        }),
        ('Date Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(owner=request.user)

    def save_model(self, request, obj, form, change):
        if not obj.owner_id:
            obj.owner = request.user
        super().save_model(request, obj, form, change)

class CompanyNotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at', 'updated_at')

admin.site.register(Task, TaskAdmin)
admin.site.register(CompanyNotification, CompanyNotificationAdmin)
admin.site.register(SubTask)

