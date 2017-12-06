from django.contrib import admin
from .models import Category, SubCategory, Phone, Advert

# Register your models here.
admin.site.register(Category)
admin.site.register(SubCategory)
admin.site.register(Phone)
admin.site.register(Advert)
