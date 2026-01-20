from django.urls import path
from .views import StartConversationView, SendMessageView,InboxView

urlpatterns = [
    path('start/', StartConversationView.as_view()),
    path('<int:conversation_id>/send/', SendMessageView.as_view()),
    path('start/', StartConversationView.as_view()),
    path('inbox/', InboxView.as_view()),
    
]


