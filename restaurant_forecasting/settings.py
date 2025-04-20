import os  # Import the os module
import secrets  # Import the secrets module

# Print a securely generated token
print(secrets.token_urlsafe(50))

# Define BASE_DIR if not already defined
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Add SECRET_KEY setting
SECRET_KEY = 'your-unique-secret-key'
# Replace 'your-unique-secret-key' with a securely generated key.
# You can generate one using Django's `secrets` module or online tools.

# Add to INSTALLED_APPS list
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'ingredient_forecast',
    'rest_framework',
]

# Middleware settings
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',  # Added SessionMiddleware
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',  # AuthenticationMiddleware remains here
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# URL configuration
ROOT_URLCONF = 'restaurant_forecasting.urls'

# Templates settings
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],  # Add your templates directory here
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# Media files settings
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Static files settings
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# Database settings
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Allowed hosts setting
ALLOWED_HOSTS = ['restaurant-ingredient-forecasting-system.onrender.com', 'localhost', '127.0.0.1']
  # Add your domain or IP here

# Debug setting
DEBUG = True

# Forecast settings
FORECAST_MONTHS = 3
HISTORICAL_MONTHS = 6


