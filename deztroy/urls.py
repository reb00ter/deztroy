"""deztroy URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
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
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views


from u24.views import CategoriesJSON, Index, AdsJSON, AdvertCreate, AdvertUpdate, AdvertDelete, cron, start_all, \
    stop_all, reset_all, push_now

urlpatterns = [
    path('', Index.as_view(), name='index'),
    path('user/', auth_views.LoginView.as_view(), name="login"),
    path('logoff/', auth_views.LogoutView.as_view(), name="logout"),
    path('json/categories', CategoriesJSON.as_view(), name='categories_json'),
    path('json/ads', AdsJSON.as_view(), name='ads_json'),
    path('cron', cron, name='cron'),
    path('stop_all', stop_all, name='stop_all'),
    path('start_all', start_all, name='start_all'),
    path('reset_all', reset_all, name='reset_all'),
    path('push_now', push_now, name='push_now'),
    path('ad/create', AdvertCreate.as_view(
        extra_context={'title': "Добавить объявление", 'submit': "Добавить"}), name='create_ad'),
    path('ad/<int:pk>/update', AdvertUpdate.as_view(
        extra_context={'title': "Править объявление", 'submit': "Сохранить"}), name='update_ad'),
    path('ad/<int:pk>/delete', AdvertDelete.as_view(), name='delete_ad'),
    path('admin/', admin.site.urls),

] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) \
              + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
