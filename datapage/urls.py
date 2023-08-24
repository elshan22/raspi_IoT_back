from django.urls import path
from .views import SensorView, DataView

urlpatterns = [
    path('updateData/<int:node_id>/', SensorView.as_view()),
    path('getData/<int:node_id>/<str:start_date>/<str:end_date>/', DataView.as_view()),
]
