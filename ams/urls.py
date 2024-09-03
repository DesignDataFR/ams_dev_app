from django.urls import path
from . import views

urlpatterns = [
    path('', views.Home, name='Home'),  
    path('Data/', views.Data, name='Data'), 
    path('alert/<str:alert_id>/', views.alert_detail, name='alert_detail'),
    path('bulk_update/', views.bulk_update, name='bulk_update'),
    path('Home/', views.Home, name='Home'), 
]
