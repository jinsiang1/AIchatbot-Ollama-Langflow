from django.urls import path, include
from . import views
from django.urls import path
app_name = 'user'
from .views import upload, delete_pdf, view_pdfs
from .views import upload_pdf

urlpatterns = [
    # Basic function
    path('login', views.login, name='login'),
    path('logout', views.logout_view, name='logout'),

    path('upload', views.upload_pdf, name='upload_pdf'),

    path('upload_pdf_page', views.upload, name='upload_pdf_page'),
    path('view_pdf', views.view_pdfs, name='view_pdfs'),
    path('delete/<int:id>/', views.delete_pdf, name='delete_pdf'),

    path('admin/staff/', include([
        path('register_staff', views.register_staff, name='register_staff'),
        path('user_list', views.user_list, name='user_list'),
        path('delete/<int:user_id>/', views.delete_user, name='delete_user'),

    ])),
]
