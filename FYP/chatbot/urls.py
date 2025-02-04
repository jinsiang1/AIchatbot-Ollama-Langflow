from django.urls import path
from . import views

app_name = 'chatbot'

urlpatterns = [
    path('', views.index, name='index'),
    path('run_flow', views.handle_flow, name='handle_flow'),
    path('get_chats', views.get_chats, name='get_chats'),
    path('clear_session', views.clear_session, name='clear_session'),
    path('chathistory_panel', views.chathistory_panel, name='chathistory_panel'),
    path('delete_session_chats/<str:session_id>', views.delete_session_chats, name='delete_session_chats'),

]
