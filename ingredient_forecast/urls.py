from django.urls import path
from . import views
from .views import save_general_settings
from .views import ContributorsView

app_name = 'ingredient_forecast'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('forecast/', views.ForecastListView.as_view(), name='forecast_list'),
    path('forecast/settings/', views.ForecastSettingsView.as_view(), name='forecast_settings'),
    path('forecast/costs/', views.IngredientCostForecastView.as_view(), name='cost_forecast'),
    path('save-general-settings/', save_general_settings, name='save_general_settings'),
    path('contributors/', ContributorsView.as_view(), name='contributors'),
]