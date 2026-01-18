import math
from datetime import date, datetime, timedelta

from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render

from .models import Booking, BusinessSpace, Category


# Create your views here.
def login(request):
    if request.method == "GET":
        storage = messages.get_messages(request)
        storage.used = True

    if request.method == "POST":
        username_or_email = request.POST.get("username")
        pword = request.POST.get("password")

        # Find username if email was entered
        if "@" in username_or_email:
            try:
                user_obj = User.objects.get(email=username_or_email)
                username = user_obj.username
            except User.DoesNotExist:
                username = username_or_email
        else:
            username = username_or_email

        user = authenticate(request, username=username, password=pword)

        if user is not None:
            auth_login(request, user)  # Use auth_login to avoid name conflict with view
            return redirect("home")
        else:
            messages.error(request, "Invalid credentials")
            return redirect("login")

    return render(request, "login.html")


def register(request):
    if request.method == "GET":
        storage = messages.get_messages(request)
        storage.used = True

    if request.method == "POST":
        uname = request.POST.get("username")
        email = request.POST.get("email")
        pword = request.POST.get("password")
        cpword = request.POST.get("cpassword")  # Confirm password

        # 1. Validation Checks
        if User.objects.filter(username=uname).exists():
            messages.error(request, "Username already taken")
            return redirect("register")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered")
            return redirect("register")

        if pword != cpword:
            messages.error(request, "Passwords do not match")
            return redirect("register")

        # 2. Create User (Hashed Password)
        new_user = User.objects.create_user(username=uname, email=email, password=pword)
        new_user.save()

        messages.success(request, "Registration successful! Please login.")
        return redirect("login")

    return render(request, "register.html")


def home(request):
    return render(request, "index.html")


def rentals(request):
    category = Category.objects.all()
    return render(request, "rentals.html", {"category": category})


@login_required(login_url="login")
def booking(request, space_id):
    storage = messages.get_messages(request)
    list(storage)
    space = get_object_or_404(BusinessSpace, id=space_id)
    today = date.today()

    context = {"space": space, "min_date": today}

    if request.method == "POST":
        action = request.POST.get("action")
        from_date_str = request.POST.get("from_date")
        to_date_str = request.POST.get("to_date")

        # Validation: Check if dates are provided
        if not from_date_str or not to_date_str:
            messages.error(request, "Please select both from and to dates")
            return render(request, "booking.html", context)

        context.update(
            {"from_date": from_date_str, "to_date": to_date_str, "checked": True}
        )

        try:
            from_date = datetime.strptime(from_date_str, "%Y-%m-%d").date()
            to_date = datetime.strptime(to_date_str, "%Y-%m-%d").date()
        except ValueError:
            messages.error(request, "Invalid date format")
            return render(request, "booking.html", context)

        # CONSTRAINT 1: From date must be today or future
        if from_date < today:
            messages.error(request, "From date cannot be in the past")
            return render(request, "booking.html", context)

        # CONSTRAINT 2: To date must be after from date
        if from_date > to_date:
            messages.error(request, "To date must be after from date")
            return render(request, "booking.html", context)

        # Additional: Same day booking check (optional - remove if you allow same day)
        if from_date == to_date:
            messages.error(request, "Booking must be for at least 2 days")
            return render(request, "booking.html", context)

        # total days
        days = (to_date - from_date).days + 1

        # cost calculation
        if space.rent_type == "Day Wise":
            total_cost = days * space.cost
        elif space.rent_type == "Week Wise":
            weeks = math.ceil(days / 7)
            total_cost = weeks * space.cost
        elif space.rent_type == "Hour Wise":
            total_cost = space.cost
        elif space.rent_type == "SqFt":
            total_cost = days * space.cost
        else:
            total_cost = 0

        # CONSTRAINT 3: Better availability check - find conflicting bookings
        conflicting_bookings = Booking.objects.filter(
            space=space, from_date__lte=to_date, to_date__gte=from_date
        )

        is_booked = conflicting_bookings.exists()

        if action == "check":
            context.update(
                {
                    "available": not is_booked and space.availability,
                    "days": days,
                    "total_cost": total_cost,
                }
            )

            # Show next available date if booked
            if is_booked:
                last_booking = conflicting_bookings.order_by("-to_date").first()
                next_available = last_booking.to_date + timedelta(days=1)
                context["next_available"] = next_available

                # Check if there's another booking after this
                next_booking = (
                    Booking.objects.filter(
                        space=space, from_date__gt=last_booking.to_date
                    )
                    .order_by("from_date")
                    .first()
                )

                if next_booking:
                    # Calculate day before next booking
                    next_booking_end = next_booking.from_date - timedelta(days=1)
                    context["next_booking_start"] = next_booking_end

            return render(request, "booking.html", context)

        elif action == "confirm":
            if not space.availability:
                messages.error(request, "This space is not available for rent")
                return render(request, "booking.html", context)
            elif is_booked:
                conflicting = conflicting_bookings.first()
                messages.error(
                    request,
                    f"Space already booked from {conflicting.from_date} to {conflicting.to_date}",
                )
                return render(request, "booking.html", context)
            else:
                # Store booking details in session not DB yet
                request.session["pending_booking"] = {
                    "space_id": space.id,
                    "from_date": from_date_str,
                    "to_date": to_date_str,
                    "total_cost": str(total_cost),
                    "days": days,
                }
                # Redirect to payment page
                return redirect("payment_new")  # New URL for payment

    return render(request, "booking.html", context)


def rentalsview(request, category):
    if not Category.objects.filter(category=category).exists():
        messages.warning(request, "No such category found")
        return redirect("rentals")

    business_spaces = BusinessSpace.objects.filter(category__category=category)

    for space in business_spaces:
        # Default values
        space.status = "available"
        space.booked_till = None
        space.available_from = date.today()

        if space.availability:
            last_booking = (
                Booking.objects.filter(space=space).order_by("-to_date").first()
            )

            if last_booking:
                space.status = "booked"
                space.booked_till = last_booking.to_date
                space.available_from = last_booking.to_date + timedelta(days=1)
        else:
            space.status = "not_rentable"

    return render(
        request,
        "products/index.html",
        {
            "businessSpace": business_spaces,
            "category": category,
        },
    )


@login_required(login_url="login")
def payment(request):
    # Get pending booking from session
    pending = request.session.get("pending_booking")

    if not pending:
        messages.error(request, "No pending booking found")
        return redirect("rentals")

    space = get_object_or_404(BusinessSpace, id=pending["space_id"])

    context = {
        "space": space,
        "from_date": pending["from_date"],
        "to_date": pending["to_date"],
        "total_cost": pending["total_cost"],
        "days": pending["days"],
    }

    return render(request, "payment.html", context)


@login_required(login_url="login")
def process_payment(request):
    if request.method == "POST":
        pending = request.session.get("pending_booking")

        if not pending:
            messages.error(request, "No pending booking found")
            return redirect("rentals")

        space = get_object_or_404(BusinessSpace, id=pending["space_id"])
        from_date = datetime.strptime(pending["from_date"], "%Y-%m-%d").date()
        to_date = datetime.strptime(pending["to_date"], "%Y-%m-%d").date()

        # Check availability again before locking
        conflicting = Booking.objects.filter(
            space=space,
            from_date__lte=to_date,
            to_date__gte=from_date,
            is_paid=True,  # Only check paid bookings
        ).exists()

        if conflicting:
            messages.error(
                request, "Sorry, this space was just booked by someone else!"
            )
            del request.session["pending_booking"]
            return redirect("rentals")

        # NOW create the booking (locked!)
        booking = Booking.objects.create(
            user=request.user,
            space=space,
            from_date=from_date,
            to_date=to_date,
            total_cost=pending["total_cost"],
            is_paid=True,  # Mark as paid immediately
        )

        # Clear session
        del request.session["pending_booking"]

        messages.success(
            request,
            "Booking confirmed successfully! Check 'Your Bookings' to view details.",
        )
        return render(request, "payment_success.html", {"booking": booking})

    return redirect("home")


@login_required(login_url="login")
def my_bookings(request):
    bookings = Booking.objects.filter(user=request.user).order_by("-created_at")

    return render(request, "my_bookings.html", {"bookings": bookings})


@login_required(login_url="login")
def invoice(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)

    context = {
        "booking": booking,
        "space": booking.space,
        "invoice_number": f"INV-{booking.id:05d}",
        "invoice_date": booking.created_at,
    }

    return render(request, "invoice.html", context)


def logout_page(request):
    auth_logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("home")  # Or redirect to 'home'
