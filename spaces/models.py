import datetime
import os

from django.contrib.auth.models import User
from django.db import models


# Create your models here.
def getFilename(request, filename):
    now = datetime.datetime.now().strftime("%Y%m%d%H:%M:%S")
    new_filename = "%s%s" % (now, filename)
    return os.path.join("uploads/", new_filename)


class Category(models.Model):
    # Category choices for identification
    SPACE_CATEGORIES = [
        ("SHOP_S", "Shop - Small"),
        ("SHOP_M", "Shop - Medium"),
        ("SHOP_L", "Shop - Large"),
        ("ATRIUM_NW", "Atrium - North & West"),
        ("ATRIUM_S", "Atrium - South"),
        ("CINEMA", "Cinema Theater"),
        ("MARKETING", "Marketing Banners"),
    ]

    category = models.CharField(max_length=20, choices=SPACE_CATEGORIES)
    description = models.TextField()
    cost_per_unit = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.category}"


class BusinessSpace(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    # Category choices for identification
    DURATION_CHOICES = [
        ("Week Days", "Week Days"),
        ("Week Ends", "Week Ends"),
        ("Public Holidays", "Public Holidays"),
        ("All Days", "All Days"),
    ]

    RENT_UNIT_CHOICES = [
        ("Day Wise", "Day Wise"),
        ("Hour Wise", "Hour Wise"),
        ("Week Wise", "Week Wise"),
        ("SqFt", "Per SqFt per Day"),
    ]
    name = models.CharField(max_length=255, null=False, blank=False)
    image = models.ImageField(upload_to=getFilename, null=True, blank=True)
    description = models.TextField()
    duration_type = models.CharField(max_length=50, choices=DURATION_CHOICES)
    rent_type = models.CharField(max_length=50, choices=RENT_UNIT_CHOICES)
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    availability = models.BooleanField(
        default=True, help_text="0-not available, 1-available"
    )


class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    space = models.ForeignKey(BusinessSpace, on_delete=models.CASCADE)
    from_date = models.DateField()
    to_date = models.DateField()
    total_cost = models.DecimalField(max_digits=10, decimal_places=2)
    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.space.name} ({self.from_date} - {self.to_date})"
