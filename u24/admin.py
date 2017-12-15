from django.contrib import admin
from .models import Category, SubCategory, Phone, Advert

# Register your models here.
admin.site.register(Category)
admin.site.register(SubCategory)
admin.site.register(Phone)


class AdvertAdmin(admin.ModelAdmin):
    list_display = ('title', 'subcategory', 'status', 'last_post')
    list_filter = ('subcategory',)


admin.site.register(Advert, AdvertAdmin)
