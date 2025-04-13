from django.shortcuts import render, redirect
from django.views.generic import TemplateView, ListView, DetailView, FormView
from django.http import JsonResponse, HttpResponse
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Sum, Count, F, Value
from django.views.decorators.csrf import csrf_exempt
from .models import Ingredient, MenuItem, Recipe, Category, Order, ForecastSettings
from .services import ForecastingService
import pandas as pd
from datetime import datetime, timedelta
import json
from django import forms

class ForecastSettingsForm(forms.ModelForm):
    class Meta:
        model = ForecastSettings
        fields = ['forecast_months', 'confidence_interval', 'seasonal_period', 'use_historical_months']
        widgets = {
            'forecast_months': forms.NumberInput(attrs={'min': 1, 'max': 12}),
            'confidence_interval': forms.NumberInput(attrs={'min': 0.5, 'max': 0.99, 'step': 0.01}),
            'seasonal_period': forms.NumberInput(attrs={'min': 1, 'max': 30}),
            'use_historical_months': forms.NumberInput(attrs={'min': 1, 'max': 24})
        }

class DashboardView(TemplateView):
    template_name = 'ingredient_forecast/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get counts for main entities
        context['ingredient_count'] = Ingredient.objects.count()
        context['menu_item_count'] = MenuItem.objects.count()
        context['active_menu_items'] = MenuItem.objects.filter(is_active=True).count()
        context['category_count'] = Category.objects.count()
        
        # Get recent orders
        context['recent_orders'] = Order.objects.select_related('menu_item').order_by('-date')[:10]
        
        # Get settings
        context['settings'], _ = ForecastSettings.objects.get_or_create(id=1)
        
        return context

class ForecastListView(ListView):
    template_name = 'ingredient_forecast/forecast_list.html'
    context_object_name = 'forecasts'
    model = Ingredient  # Not actually used, but needed for ListView
    
    def get_queryset(self):
        # We'll override this to return our custom data
        return []
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        settings, _ = ForecastSettings.objects.get_or_create(id=1)
        months = settings.forecast_months
        
        # Get the forecast data
        forecast_df = ForecastingService.forecast_ingredients_needed(months)
        
        if forecast_df.empty:
            context['no_data'] = True
            return context
            
        # Convert to list of dicts for template
        forecasts = []
        
        # Group by month and ingredient
        for month in forecast_df['month'].unique():
            month_data = forecast_df[forecast_df['month'] == month]
            
            for _, row in month_data.iterrows():
                forecasts.append({
                    'month': row['month'],
                    'ingredient_name': row['ingredient_name'],
                    'quantity': row['quantity'],
                    'unit': row['unit'],
                    'ingredient_id': row['ingredient_id']
                })
        
        context['forecasts'] = forecasts
        context['months'] = sorted(forecast_df['month'].unique())
        context['settings'] = settings
        
        return context

class ForecastSettingsView(FormView):
    template_name = 'ingredient_forecast/forecast_settings.html'
    form_class = ForecastSettingsForm
    success_url = reverse_lazy('ingredient_forecast:forecast_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        settings, _ = ForecastSettings.objects.get_or_create(id=1)
        kwargs['instance'] = settings
        return kwargs
    
    def form_valid(self, form):
        form.save()
        messages.success(self.request, 'Forecast settings saved successfully!')
        return super().form_valid(form)

class IngredientCostForecastView(TemplateView):
    template_name = 'ingredient_forecast/cost_forecast.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        settings, _ = ForecastSettings.objects.get_or_create(id=1)
        months = settings.forecast_months
        
        # Get the cost forecast data
        forecast_df = ForecastingService.get_ingredient_cost_forecast(months)
        
        if forecast_df.empty:
            context['no_data'] = True
            return context
        
        # Apply filters
        request = self.request
        selected_month = request.GET.get('month')
        selected_ingredient = request.GET.get('ingredient')
        
        if selected_month:
            forecast_df = forecast_df[forecast_df['month'] == selected_month]
        if selected_ingredient:
            forecast_df = forecast_df[forecast_df['ingredient_id'] == int(selected_ingredient)]
        
        # Calculate totals by month
        monthly_totals = forecast_df.groupby('month').agg({'cost': 'sum'}).reset_index()
        monthly_totals_list = monthly_totals.to_dict('records')
        
        # Get top ingredients by cost
        top_ingredients = (
            forecast_df.groupby('ingredient_name')
            .agg({'cost': 'sum'})
            .sort_values('cost', ascending=False)
            .head(10)
            .reset_index()
        )
        
        # Convert forecast to list of dicts
        forecasts = []
        for _, row in forecast_df.iterrows():
            forecasts.append({
                'month': row['month'],
                'ingredient_name': row['ingredient_name'],
                'quantity': round(row['quantity'], 2),
                'unit': row['unit'],
                'cost': round(row['cost'], 2)
            })
        
        context['forecasts'] = forecasts
        context['monthly_totals'] = monthly_totals_list
        context['top_ingredients'] = top_ingredients.to_dict('records')
        context['settings'] = settings
        
        # Prepare chart data
        context['chart_labels'] = monthly_totals['month'].tolist()
        context['chart_data'] = monthly_totals['cost'].tolist()
        
        # Fetch dynamic ingredients for the filter
        context['ingredients'] = Ingredient.objects.all()
        
        # Generate month filter options (current month to next 4 months)
        current_date = datetime.now()
        context['months'] = [
            (current_date + timedelta(days=30 * i)).strftime('%Y-%m') for i in range(5)
        ]
        
        return context

@csrf_exempt
def save_algorithm_settings(request):
    if request.method == 'POST':
        # Process the form data here
        messages.success(request, 'Algorithm settings saved successfully!')
        return redirect('ingredient_forecast:forecast_settings')
    return HttpResponse(status=405)  # Method not allowed

@csrf_exempt
def save_factor_settings(request):
    if request.method == 'POST':
        # Process the form data here
        settings, _ = ForecastSettings.objects.get_or_create(id=1)
        settings.consider_weather = 'consider_weather' in request.POST
        settings.consider_events = 'consider_events' in request.POST
        settings.consider_seasonality = 'consider_seasonality' in request.POST
        settings.consider_trends = 'consider_trends' in request.POST
        settings.save()
        messages.success(request, 'Factor settings saved successfully!')
        return redirect('ingredient_forecast:forecast_settings')
    return HttpResponse(status=405)  # Method not allowed

@csrf_exempt
def save_general_settings(request):
    if request.method == 'POST':
        # Process the form data here
        settings, _ = ForecastSettings.objects.get_or_create(id=1)
        settings.forecast_horizon = request.POST.get('forecast_horizon', settings.forecast_horizon)
        settings.history_period = request.POST.get('history_period', settings.history_period)
        settings.update_frequency = request.POST.get('update_frequency', settings.update_frequency)
        settings.notification_threshold = request.POST.get('notification_threshold', settings.notification_threshold)
        settings.save()
        messages.success(request, 'General settings saved successfully!')
        return redirect('ingredient_forecast:forecast_settings')
    return HttpResponse(status=405)  # Method not allowed


class ContributorsView(TemplateView):
    template_name = 'ingredient_forecast/contributors.html'
