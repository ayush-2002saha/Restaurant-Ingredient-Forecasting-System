from django.contrib import admin
from .models import Category, MenuItem, Ingredient, Recipe, RecipeIngredient, Order, ForecastSettings

class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1

@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    inlines = [RecipeIngredientInline]
    list_display = ('menu_item', 'preparation_time', 'cooking_time', 'serving_size')
    search_fields = ('menu_item__name', 'instructions')

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'is_active', 'is_vegetarian', 'is_vegan', 'is_gluten_free')
    list_filter = ('category', 'is_active', 'is_vegetarian', 'is_vegan', 'is_gluten_free')
    search_fields = ('name', 'description')

@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'unit_of_measure', 'cost_per_unit', 'inventory_level', 'is_allergen')
    list_filter = ('is_allergen', 'unit_of_measure')
    search_fields = ('name', 'description')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('date', 'menu_item', 'quantity')
    list_filter = ('date', 'menu_item')
    date_hierarchy = 'date'

@admin.register(ForecastSettings)
class ForecastSettingsAdmin(admin.ModelAdmin):
    list_display = ('id', 'forecast_months', 'confidence_interval', 'seasonal_period', 'use_historical_months')