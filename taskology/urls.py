from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('user_login/', views.user_login, name='user_login'),
    path('user_logout/', views.user_logout, name='user_logout'),
    path('login_with_email/', views.login_with_email, name='login_with_email'),
    path('register/', views.user_register, name='user_register'),

    # activación de la cuenta de usuario por correo electrónico
    path('activate/<uidb64>/<token>/', views.activate, name='activate'),
    path('sending_activate_token/', views.sending_activate_token, name='sending_activate_token'),

    # Forgoten password
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='authentication/password_reset.html'), name="password_reset"),
    path('password_reset_sent/', auth_views.PasswordResetDoneView.as_view(template_name='authentication/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name="authentication/password_reset_confirm.html"), name='password_reset_confirm'),
    path('reset_password_complete/', auth_views.PasswordResetCompleteView.as_view(template_name='authentication/password_reset_complete.html'), name='password_reset_complete'),

    # Tasks
    # path('tasks/', views.tasks, name='tasks'),
    path('items/', views.update_task_order, name='update_task_order'),
    path('items_detail/<int:pk>/', views.items_detail, name='items_detail'),
    path('delete_task/<int:pk>/', views.delete_task, name='delete_task'),
    path('edit_task/<int:pk>/', views.edit_task, name='edit_task'),
    path('delete_all_tasks/', views.delete_all_tasks, name='delete_all_tasks'),

    path('dashboard/', views.dashboard, name='dashboard'),

    # tasks check list
    path('all_tasks/', views.all_tasks, name='all_tasks'),
    path('delete_task_ck/<int:pk>/', views.delete_task_ck, name='delete_task_ck'),
    path('edit_task_ck/<int:pk>/', views.edit_task_ck, name='edit_task_ck'),
    path('complete-task/<int:task_id>/', views.complete_task, name='complete_task'),

    path('create_subtask/', views.create_subtask, name='create_subtask'),


    path('notifications/', views.all_notifications, name='all_notifications'),
    path('notification/<int:pk>/', views.notification_detail, name='notification_detail'),

    path('public_privacy_policy/', views.public_privacy_policy, name='public_privacy_policy'), 
    path('public_terms_of_service/', views.public_terms_of_service, name='public_terms_of_service'), 
]