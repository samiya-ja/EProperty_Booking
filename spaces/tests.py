from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Booking, BusinessSpace, Category


class CategoryModelTest(TestCase):
    def test_category_creation(self):
        category = Category.objects.create(
            category="SHOP_S", description="Small shop", cost_per_unit=Decimal("100.00")
        )
        self.assertEqual(category.category, "SHOP_S")


class BusinessSpaceModelTest(TestCase):
    def test_space_creation(self):
        category = Category.objects.create(
            category="SHOP_M",
            description="Medium shop",
            cost_per_unit=Decimal("200.00"),
        )
        space = BusinessSpace.objects.create(
            category=category,
            name="Shop A1",
            description="Prime shop",
            duration_type="All Days",
            rent_type="Day Wise",
            cost=Decimal("500.00"),
            availability=True,
        )
        self.assertEqual(space.name, "Shop A1")
        self.assertTrue(space.availability)


class BookingModelTest(TestCase):
    def test_booking_creation(self):
        user = User.objects.create_user(username="testuser", password="testpass")
        category = Category.objects.create(
            category="CINEMA", description="Cinema", cost_per_unit=Decimal("1000.00")
        )
        space = BusinessSpace.objects.create(
            category=category,
            name="Cinema 1",
            description="Cinema hall",
            duration_type="All Days",
            rent_type="Day Wise",
            cost=Decimal("2000.00"),
        )
        booking = Booking.objects.create(
            user=user,
            space=space,
            from_date=date.today(),
            to_date=date.today() + timedelta(days=2),
            total_cost=Decimal("4000.00"),
        )
        self.assertEqual(booking.user.username, "testuser")


class LoginViewTest(TestCase):
    def test_login_page(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)

    def test_login_success(self):
        User.objects.create_user(username="testuser", password="testpass")
        response = self.client.post(
            reverse("login"), {"username": "testuser", "password": "testpass"}
        )
        self.assertEqual(response.status_code, 302)


class RegisterViewTest(TestCase):
    def test_register_page(self):
        response = self.client.get(reverse("register"))
        self.assertEqual(response.status_code, 200)

    def test_register_new_user(self):
        self.client.post(
            reverse("register"),
            {
                "username": "newuser",
                "email": "new@test.com",
                "password": "pass123",
                "cpassword": "pass123",
            },
        )
        self.assertTrue(User.objects.filter(username="newuser").exists())


class HomeViewTest(TestCase):
    def test_home_page(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)


class RentalsViewTest(TestCase):
    def test_rentals_page(self):
        response = self.client.get(reverse("rentals"))
        self.assertEqual(response.status_code, 200)


class BookingViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.category = Category.objects.create(
            category="ATRIUM_S", description="Atrium", cost_per_unit=Decimal("500.00")
        )
        self.space = BusinessSpace.objects.create(
            category=self.category,
            name="Atrium 1",
            description="Nice atrium",
            duration_type="All Days",
            rent_type="Day Wise",
            cost=Decimal("1000.00"),
        )

    def test_booking_requires_login(self):
        response = self.client.get(
            reverse("booking", kwargs={"space_id": self.space.id})
        )
        self.assertEqual(response.status_code, 302)

    def test_booking_page_loads(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(
            reverse("booking", kwargs={"space_id": self.space.id})
        )
        self.assertEqual(response.status_code, 200)


class MyBookingsViewTest(TestCase):
    def test_my_bookings_requires_login(self):
        response = self.client.get(reverse("my_bookings"))
        self.assertEqual(response.status_code, 302)

    def test_booking_cost_calculation(self):
            """Test if the total cost is calculated correctly for 3 days"""
            self.client.login(username="testuser", password="testpass")
            
            # We simulate a 3-day booking (Today, Tomorrow, Day after)
            # 1000 per day * 3 days should = 3000
            from_date = date.today()
            to_date = date.today() + timedelta(days=2) 
            
            response = self.client.post(
                reverse("booking", kwargs={"space_id": self.space.id}),
                {
                    "action": "check",
                    "from_date": from_date.strftime("%Y-%m-%d"),
                    "to_date": to_date.strftime("%Y-%m-%d"),
                }
            )
            
            # Check if the calculated cost in the context is exactly 3000
            self.assertEqual(response.context['total_cost'], Decimal("3000.00"))
            self.assertEqual(response.context['days'], 3)