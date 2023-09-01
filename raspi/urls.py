from django.contrib import admin
from django.urls import path, include
from .views import RaspberryPiInfoView, NodeView, ThemeView, LoginView
from commandpage.views import TasksView, ConditionalTasksView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('report/', include('datapage.urls')),
    path('command/', include('commandpage.urls')),
    path('name/', RaspberryPiInfoView.as_view()),
    path('tasks/', TasksView.as_view()),
    path('tasks/cond/', ConditionalTasksView.as_view()),
    path('nodes/<str:node_type>/', NodeView.as_view()),
    path('theme/', ThemeView.as_view()),
    path('connect/', LoginView.as_view()),
    path('getStatus/', LoginView.as_view()),
]
