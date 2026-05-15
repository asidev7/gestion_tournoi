from django.urls import path
from . import views

urlpatterns = [
    path('', views.predictions_list, name='predictions'),
    path('match/<int:match_pk>/', views.make_prediction, name='make_prediction'),
    path('mes-pronostics/', views.my_predictions, name='my_predictions'),
]
