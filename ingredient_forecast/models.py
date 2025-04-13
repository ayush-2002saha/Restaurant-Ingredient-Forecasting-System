from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=200, blank=True, null=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Categories"

class MenuItem(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    price = models.FloatField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="menu_items")
    is_vegetarian = models.BooleanField(default=False)
    is_vegan = models.BooleanField(default=False)
    is_gluten_free = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    image_path = models.CharField(max_length=255, blank=True, null=True)
    
    def __str__(self):
        return f"{self.name} (${self.price})"

class Ingredient(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    unit_of_measure = models.CharField(max_length=50)
    cost_per_unit = models.FloatField(null=True, blank=True)
    is_allergen = models.BooleanField(default=False)
    inventory_level = models.FloatField(default=0)
    
    def __str__(self):
        return f"{self.name} ({self.unit_of_measure})"

class Recipe(models.Model):
    menu_item = models.OneToOneField(MenuItem, on_delete=models.CASCADE, related_name="recipe")
    preparation_time = models.IntegerField(help_text="in minutes", null=True, blank=True)
    cooking_time = models.IntegerField(help_text="in minutes", null=True, blank=True)
    instructions = models.TextField()
    serving_size = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    ingredients = models.ManyToManyField(Ingredient, through='RecipeIngredient')
    
    def __str__(self):
        return f"Recipe for {self.menu_item.name}"

class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name="recipe_ingredients")
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE, related_name="recipe_ingredients")
    quantity = models.FloatField()
    preparation_notes = models.CharField(max_length=255, blank=True, null=True)
    
    def __str__(self):
        return f"{self.ingredient.name}: {self.quantity} {self.ingredient.unit_of_measure}"

class Order(models.Model):
    """Track historical orders for forecasting"""
    date = models.DateField()
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name="orders")
    quantity = models.IntegerField()
    
    def __str__(self):
        return f"{self.quantity}x {self.menu_item.name} on {self.date}"

class ForecastSettings(models.Model):
    """Settings for the forecasting algorithm"""
    forecast_months = models.IntegerField(default=3, help_text="Number of months to forecast")
    confidence_interval = models.FloatField(default=0.95, help_text="Confidence interval for forecasts (0-1)")
    seasonal_period = models.IntegerField(default=7, help_text="Days in seasonal cycle (7 for weekly patterns)")
    use_historical_months = models.IntegerField(default=6, help_text="How many months of historical data to use")
    
    def __str__(self):
        return f"Forecast Settings (v{self.id})"