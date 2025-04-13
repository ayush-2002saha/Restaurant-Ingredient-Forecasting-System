import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from .models import MenuItem, Recipe, RecipeIngredient, Order, Ingredient, ForecastSettings
from django.db.models import Sum, F, Func, FloatField
from django.db.models.functions import TruncDate

class ForecastingService:
    @staticmethod
    def get_historical_sales_data():
        """Get historical sales data grouped by date and menu item"""
        orders = Order.objects.select_related('menu_item').all()
        
        # Convert to DataFrame
        data = []
        for order in orders:
            data.append({
                'date': order.date,
                'menu_item_id': order.menu_item_id,
                'menu_item_name': order.menu_item.name,
                'quantity': order.quantity
            })
        
        df = pd.DataFrame(data)
        if df.empty:
            return pd.DataFrame()
            
        # Group by date and menu item
        grouped = df.pivot_table(
            index='date', 
            columns='menu_item_id', 
            values='quantity', 
            aggfunc='sum',
            fill_value=0
        )
        
        return grouped
    
    @staticmethod
    def forecast_menu_item_sales(months=3):
        """Forecast sales for each menu item for the next X months"""
        # Get settings
        settings, _ = ForecastSettings.objects.get_or_create(id=1)
        months = settings.forecast_months
        use_months = settings.use_historical_months
        seasonal_period = settings.seasonal_period
        
        # Get historical data
        historical_data = ForecastingService.get_historical_sales_data()
        if historical_data.empty:
            return pd.DataFrame()
        
        # Filter to only include the last 'use_months' of data
        cutoff_date = datetime.now().date() - timedelta(days=30*use_months)
        historical_data = historical_data[historical_data.index >= cutoff_date]
        
        if historical_data.empty:
            return pd.DataFrame()
        
        # Set up date range for forecast
        last_date = historical_data.index.max()
        forecast_start = last_date + timedelta(days=1)
        forecast_end = forecast_start + timedelta(days=30*months)
        forecast_dates = pd.date_range(start=forecast_start, end=forecast_end, freq='D')
        
        # Create forecasts for each menu item
        forecasts = pd.DataFrame(index=forecast_dates)
        
        for menu_item_id in historical_data.columns:
            # Get time series for this menu item
            series = historical_data[menu_item_id]
            
            # Check if we have enough data for forecasting
            if len(series) < seasonal_period * 2:
                # Not enough data, use mean
                forecasts[menu_item_id] = series.mean()
                continue
                
            try:
                # Fit Holt-Winters model
                model = ExponentialSmoothing(
                    series,
                    seasonal='add',
                    seasonal_periods=seasonal_period,
                    trend='add'
                ).fit()
                
                # Generate forecast
                forecast = model.forecast(len(forecast_dates))
                forecasts[menu_item_id] = forecast.values
                
                # Ensure no negative values
                forecasts[menu_item_id] = forecasts[menu_item_id].clip(lower=0)
                
                # Round to integers (can't sell partial menu items)
                forecasts[menu_item_id] = forecasts[menu_item_id].round()
                
            except Exception as e:
                # Fallback to simple average
                forecasts[menu_item_id] = series.mean()
        
        return forecasts
    
    @staticmethod
    def forecast_ingredients_needed(months=3):
        """Calculate forecasted ingredient needs based on menu item forecast"""
        # Get menu item sales forecast
        menu_item_forecast = ForecastingService.forecast_menu_item_sales(months)
        if menu_item_forecast.empty:
            return pd.DataFrame()
        
        # Get recipe information
        recipe_ingredients = {}
        for recipe in Recipe.objects.prefetch_related('recipe_ingredients__ingredient'):
            menu_item_id = recipe.menu_item_id
            ingredients = {}
            
            for ri in recipe.recipe_ingredients.all():
                ingredient_name = ri.ingredient.name
                quantity = ri.quantity
                unit = ri.ingredient.unit_of_measure
                
                ingredients[ingredient_name] = {
                    'quantity': quantity,
                    'unit': unit,
                    'ingredient_id': ri.ingredient_id
                }
            
            recipe_ingredients[menu_item_id] = ingredients
        
        # Calculate total ingredients needed
        ingredients_df = pd.DataFrame()
        
        # Sum forecasted quantities for each menu item
        monthly_forecast = menu_item_forecast.resample('M').sum()
        
        for month_date, row in monthly_forecast.iterrows():
            month_str = month_date.strftime('%Y-%m')
            month_data = {}
            
            for menu_item_id, quantity in row.items():
                # Skip if no recipe for this menu item
                if menu_item_id not in recipe_ingredients:
                    continue
                
                # Get ingredients for this menu item
                menu_ingredients = recipe_ingredients[menu_item_id]
                
                # Calculate ingredients needed
                for ingredient_name, details in menu_ingredients.items():
                    ingredient_qty = details['quantity'] * quantity
                    
                    if ingredient_name in month_data:
                        month_data[ingredient_name]['quantity'] += ingredient_qty
                    else:
                        month_data[ingredient_name] = {
                            'quantity': ingredient_qty,
                            'unit': details['unit'],
                            'ingredient_id': details['ingredient_id']
                        }
            
            # Add to dataframe
            for ingredient_name, details in month_data.items():
                ingredients_df = pd.concat([ingredients_df, pd.DataFrame({
                    'month': [month_str],
                    'ingredient_name': [ingredient_name],
                    'quantity': [details['quantity']],
                    'unit': [details['unit']],
                    'ingredient_id': [details['ingredient_id']]
                })])
        
        return ingredients_df

    @staticmethod
    def get_ingredient_cost_forecast(months=3):
        """Calculate forecasted ingredient costs"""
        # Get ingredient forecast
        ingredients_forecast = ForecastingService.forecast_ingredients_needed(months)
        if ingredients_forecast.empty:
            return pd.DataFrame()
        
        # Get ingredient costs
        ingredient_costs = {}
        for ingredient in Ingredient.objects.all():
            ingredient_costs[ingredient.id] = ingredient.cost_per_unit or 0
        
        # Calculate costs
        ingredients_forecast['cost'] = ingredients_forecast.apply(
            lambda row: row['quantity'] * ingredient_costs.get(row['ingredient_id'], 0),
            axis=1
        )
        
        return ingredients_forecast