"""
Django Management Command to add sample data selectively
without clearing existing data.

Usage:
    python manage.py add_sample_data --customers 5
    python manage.py add_sample_data --vendors 2
    python manage.py add_sample_data --food-items 10
    python manage.py add_sample_data --orders 5
    python manage.py add_sample_data --all
"""

import os
import random
from decimal import Decimal
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Point
from django.utils.text import slugify
from django.core.files import File
from django.conf import settings

from accounts.models import User, UserProfile
from vendor.models import Vendor, OpeningHour
from menu.models import Category, FoodItem
from orders.models import Order, Payment, OrderedFood
from recommendations.models import Review, UserActivity


class Command(BaseCommand):
    help = 'Add sample data to existing database without clearing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--customers',
            type=int,
            help='Number of customers to add',
        )
        parser.add_argument(
            '--vendors',
            type=int,
            help='Number of vendors to add',
        )
        parser.add_argument(
            '--food-items',
            type=int,
            help='Number of food items to add to existing vendors',
        )
        parser.add_argument(
            '--orders',
            type=int,
            help='Number of orders to create',
        )
        parser.add_argument(
            '--reviews',
            type=int,
            help='Number of reviews to add',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Add a small amount of all data types',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Adding sample data...'))

        if options['all']:
            self.add_customers(3)
            self.add_vendors(1)
            self.add_food_items(10)
            self.add_orders(3)
            self.add_reviews(5)
        else:
            if options['customers']:
                self.add_customers(options['customers'])
            if options['vendors']:
                self.add_vendors(options['vendors'])
            if options['food_items']:
                self.add_food_items(options['food_items'])
            if options['orders']:
                self.add_orders(options['orders'])
            if options['reviews']:
                self.add_reviews(options['reviews'])

        self.stdout.write(self.style.SUCCESS('✅ Sample data added successfully!'))

    def add_customers(self, count):
        """Add customer users"""
        self.stdout.write(f'Adding {count} customers...')

        first_names = ['Alex', 'Chris', 'Taylor', 'Jordan', 'Morgan', 'Casey', 'Riley', 'Avery', 'Quinn', 'Blake']
        last_names = ['Anderson', 'Thomas', 'Jackson', 'White', 'Harris', 'Martin', 'Garcia', 'Martinez', 'Robinson', 'Clark']

        created = 0
        for i in range(count):
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            email = f"{first_name.lower()}.{last_name.lower()}{random.randint(1, 999)}@example.com"

            if User.objects.filter(email=email).exists():
                continue

            username = f"{first_name.lower()}.{last_name.lower()}{random.randint(1, 9999)}"

            user = User.objects.create_user(
                first_name=first_name,
                last_name=last_name,
                username=username,
                email=email,
                password='customer123'
            )
            user.role = User.CUSTOMER
            user.phone_number = f"{random.randint(1000000000, 9999999999)}"
            user.is_active = True
            user.save()

            UserProfile.objects.create(
                user=user,
                address=f"{random.randint(100, 9999)} {random.choice(['Main', 'Oak', 'Pine', 'Maple', 'Elm'])} Street",
                country="USA",
                state="California",
                city=random.choice(['San Francisco', 'Los Angeles', 'San Diego', 'Oakland']),
                pin_code=f"{random.randint(90000, 99999)}",
                latitude=str(37.7749 + random.uniform(-0.5, 0.5)),
                longitude=str(-122.4194 + random.uniform(-0.5, 0.5))
            )
            created += 1

        self.stdout.write(self.style.SUCCESS(f'✅ Created {created} customers'))

    def add_vendors(self, count):
        """Add vendor restaurants"""
        self.stdout.write(f'Adding {count} vendors...')

        restaurant_types = ['Bistro', 'Cafe', 'Kitchen', 'Grill', 'Palace', 'Corner', 'House', 'Express']
        cuisine_types = ['Thai', 'Indian', 'Greek', 'French', 'Vietnamese', 'Korean', 'Spanish', 'American']

        created = 0
        for i in range(count):
            cuisine = random.choice(cuisine_types)
            rest_type = random.choice(restaurant_types)
            vendor_name = f"{cuisine} {rest_type}"

            # Create vendor user
            email = f"{slugify(vendor_name).replace('-', '.')}@restaurant.com"
            if User.objects.filter(email=email).exists():
                email = f"{slugify(vendor_name).replace('-', '.')}{random.randint(1, 99)}@restaurant.com"

            username = slugify(vendor_name).replace('-', '.')

            user = User.objects.create_user(
                first_name=cuisine,
                last_name=rest_type,
                username=username,
                email=email,
                password='vendor123'
            )
            user.role = User.VENDOR
            user.phone_number = f"{random.randint(1000000000, 9999999999)}"
            user.is_active = True
            user.save()

            # Create user profile
            user_profile = UserProfile.objects.create(
                user=user,
                address=f"{random.randint(100, 9999)} Restaurant Row",
                country="USA",
                state="California",
                city="San Francisco",
                pin_code=f"{random.randint(94100, 94199)}",
                latitude=str(37.7749 + random.uniform(-0.2, 0.2)),
                longitude=str(-122.4194 + random.uniform(-0.2, 0.2))
            )

            # Create vendor
            vendor = Vendor.objects.create(
                user=user,
                user_profile=user_profile,
                vendor_name=vendor_name,
                vendor_slug=slugify(vendor_name) + f"-{random.randint(1, 9999)}",
                is_approved=True
            )

            # Add opening hours
            for day in range(1, 8):
                if day != 7:  # Not Sunday
                    OpeningHour.objects.create(
                        vendor=vendor,
                        day=day,
                        from_hour='09:00 AM',
                        to_hour='10:00 PM',
                        is_closed=False
                    )

            # Add categories
            category_names = random.sample(['Pizza', 'Burgers', 'Chicken', 'Seafood', 'Vegetarian', 'Desserts'], 3)
            for cat_name in category_names:
                Category.objects.create(
                    vendor=vendor,
                    category_name=cat_name,
                    slug=f"{slugify(cat_name)}-{vendor.id}",
                    description=f"Delicious {cat_name.lower()} dishes"
                )

            created += 1

        self.stdout.write(self.style.SUCCESS(f'✅ Created {created} vendors'))

    def add_food_items(self, count):
        """Add food items to existing vendors"""
        self.stdout.write(f'Adding {count} food items...')

        vendors = list(Vendor.objects.filter(is_approved=True))
        if not vendors:
            self.stdout.write(self.style.ERROR('❌ No approved vendors found. Create vendors first.'))
            return

        food_adjectives = ['Delicious', 'Tasty', 'Crispy', 'Fresh', 'Grilled', 'Fried', 'Spicy', 'Sweet', 'Savory']
        food_bases = ['Sandwich', 'Salad', 'Wrap', 'Soup', 'Pasta', 'Noodles', 'Curry', 'Stir-fry', 'Platter']

        created = 0
        for i in range(count):
            vendor = random.choice(vendors)
            categories = list(Category.objects.filter(vendor=vendor))

            if not categories:
                continue

            category = random.choice(categories)
            food_name = f"{random.choice(food_adjectives)} {category.category_name} {random.choice(food_bases)}"

            food_item = FoodItem.objects.create(
                vendor=vendor,
                category=category,
                food_title=food_name,
                slug=slugify(food_name) + f"-{vendor.id}-{random.randint(1, 9999)}",
                description=f"Amazing {food_name.lower()} prepared with fresh ingredients",
                price=Decimal(str(random.uniform(8.99, 29.99))).quantize(Decimal('0.01')),
                is_available=True
            )
            created += 1

        self.stdout.write(self.style.SUCCESS(f'✅ Created {created} food items'))

    def add_orders(self, count):
        """Add sample orders"""
        self.stdout.write(f'Adding {count} orders...')

        customers = list(User.objects.filter(role=User.CUSTOMER, is_active=True))
        vendors = list(Vendor.objects.filter(is_approved=True))

        if not customers:
            self.stdout.write(self.style.ERROR('❌ No customers found. Create customers first.'))
            return

        if not vendors:
            self.stdout.write(self.style.ERROR('❌ No vendors found. Create vendors first.'))
            return

        created = 0
        for i in range(count):
            customer = random.choice(customers)
            customer_profile = UserProfile.objects.get(user=customer)

            # Create payment
            payment = Payment.objects.create(
                user=customer,
                transaction_id=f'TXN{random.randint(100000, 999999)}',
                payment_method=random.choice(['Stripe', 'SSLCommerz']),
                amount=str(random.randint(20, 150)),
                status='Completed'
            )

            # Create order
            order = Order.objects.create(
                user=customer,
                payment=payment,
                order_number=f'ORD{random.randint(10000, 99999)}',
                first_name=customer.first_name,
                last_name=customer.last_name,
                phone=customer.phone_number,
                email=customer.email,
                address=customer_profile.address,
                country=customer_profile.country,
                state=customer_profile.state,
                city=customer_profile.city,
                pin_code=customer_profile.pin_code,
                total=0,
                total_tax=0,
                payment_method=payment.payment_method,
                status=random.choice(['New', 'Accepted', 'Completed']),
                is_ordered=True
            )

            # Add items
            vendor = random.choice(vendors)
            order.vendors.add(vendor)

            food_items = list(FoodItem.objects.filter(vendor=vendor, is_available=True))
            if food_items:
                selected_items = random.sample(food_items, min(random.randint(1, 3), len(food_items)))
                total_amount = 0

                for food_item in selected_items:
                    quantity = random.randint(1, 2)
                    price = float(food_item.price)
                    amount = price * quantity
                    total_amount += amount

                    OrderedFood.objects.create(
                        order=order,
                        payment=payment,
                        user=customer,
                        fooditem=food_item,
                        quantity=quantity,
                        price=price,
                        amount=amount
                    )

                tax = total_amount * 0.1
                order.total = total_amount
                order.total_tax = tax
                order.save()
                created += 1

        self.stdout.write(self.style.SUCCESS(f'✅ Created {created} orders'))

    def add_reviews(self, count):
        """Add reviews to completed orders"""
        self.stdout.write(f'Adding {count} reviews...')

        completed_orders = list(Order.objects.filter(status='Completed'))

        if not completed_orders:
            self.stdout.write(self.style.WARNING('⚠️  No completed orders found.'))
            return

        review_texts = [
            "Excellent food and service!",
            "Good quality, will order again.",
            "Tasty but could be better.",
            "Fresh and delicious!",
            "Highly recommended!",
            "Average experience.",
            "Great value for money.",
            "Could improve on presentation.",
        ]

        created = 0
        attempts = 0
        max_attempts = count * 3

        while created < count and attempts < max_attempts:
            attempts += 1
            order = random.choice(completed_orders)
            ordered_foods = list(OrderedFood.objects.filter(order=order))

            if not ordered_foods:
                continue

            ordered_food = random.choice(ordered_foods)

            # Check if review already exists
            if Review.objects.filter(
                user=order.user,
                fooditem=ordered_food.fooditem,
                order=order
            ).exists():
                continue

            Review.objects.create(
                user=order.user,
                fooditem=ordered_food.fooditem,
                order=order,
                rating=random.randint(3, 5),
                review_text=random.choice(review_texts)
            )
            created += 1

        self.stdout.write(self.style.SUCCESS(f'✅ Created {created} reviews'))
