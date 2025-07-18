"""
URL configuration for vices_db project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.urls import path, include
from products.openai_views import generate_recommendations

urlpatterns = [
    path('admin/', admin.site.urls),
    # path('health/', include('health.urls')),  # Health check endpoint
    path('api/users/', include('users.urls')),
    path('api/goals/', include('goals.urls')),
    path('api/tracking/', include('tracking.urls')),
    path('api/openai/', generate_recommendations, name='openai_recommendations'),
    path('dj-rest-auth/', include('dj_rest_auth.urls')),
    path('dj-rest-auth/registration/', include('dj_rest_auth.registration.urls')),
    path('dj-rest-auth/social/', include('allauth.socialaccount.urls')),
]
