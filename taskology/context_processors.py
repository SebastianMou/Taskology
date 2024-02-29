from .models import CompanyNotification

def notification_processor(request):
    # Assuming you want the 5 most recent notifications. Adjust the order_by field as needed.
    return {'notify': CompanyNotification.objects.all().order_by('-created_at')[:5]}
