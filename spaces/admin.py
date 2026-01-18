from django.contrib import admin

from .models import Booking, BusinessSpace, Category

# Register your models here.
# override the default admin panel
"""class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'image')"""

admin.site.register(Category)
admin.site.register(BusinessSpace)
admin.site.register(Booking)
