from django.urls import path
from .views import CommandView

urlpatterns = [
    path('sendData/', CommandView.as_view()),
]
