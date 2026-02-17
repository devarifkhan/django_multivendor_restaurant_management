"""
Django Management Command to seed the database with realistic data
for the multivendor restaurant management system.

Usage:
    python manage.py seed_data
    python manage.py seed_data --clear  # Clear existing data first
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
from orders.utils import generate_order_number
from recommendations.models import Review, UserActivity


class Command(BaseCommand):
    help = 'Seeds the database with realistic restaurant and food data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing data...'))
            self.clear_data()

        self.stdout.write(self.style.SUCCESS('Starting data seeding...'))

        # Seed in order of dependencies
        self.seed_users()
        self.seed_vendors()
        self.seed_categories()
        self.seed_food_items()
        self.seed_opening_hours()
        self.seed_orders()
        self.seed_reviews()
        self.seed_user_activities()

        self.stdout.write(self.style.SUCCESS('✅ Database seeding completed successfully!'))

    def clear_data(self):
        """Clear all data from the database"""
        UserActivity.objects.all().delete()
        Review.objects.all().delete()
        OrderedFood.objects.all().delete()
        Order.objects.all().delete()
        Payment.objects.all().delete()
        FoodItem.objects.all().delete()
        Category.objects.all().delete()
        OpeningHour.objects.all().delete()
        Vendor.objects.all().delete()
        UserProfile.objects.all().delete()
        User.objects.filter(is_superadmin=False).delete()
        self.stdout.write(self.style.SUCCESS('✅ Existing data cleared'))

    def seed_users(self):
        """Create users (vendors and customers)"""
        self.stdout.write('Creating users...')

        # Customer data
        customers_data = [
            {'first_name': 'John', 'last_name': 'Doe', 'email': 'john.doe@example.com', 'phone': '1234567890'},
            {'first_name': 'Jane', 'last_name': 'Smith', 'email': 'jane.smith@example.com', 'phone': '2345678901'},
            {'first_name': 'Michael', 'last_name': 'Johnson', 'email': 'michael.j@example.com', 'phone': '3456789012'},
            {'first_name': 'Emily', 'last_name': 'Williams', 'email': 'emily.w@example.com', 'phone': '4567890123'},
            {'first_name': 'David', 'last_name': 'Brown', 'email': 'david.b@example.com', 'phone': '5678901234'},
            {'first_name': 'Sarah', 'last_name': 'Davis', 'email': 'sarah.d@example.com', 'phone': '6789012345'},
            {'first_name': 'James', 'last_name': 'Miller', 'email': 'james.m@example.com', 'phone': '7890123456'},
            {'first_name': 'Lisa', 'last_name': 'Wilson', 'email': 'lisa.w@example.com', 'phone': '8901234567'},
            {'first_name': 'Robert', 'last_name': 'Moore', 'email': 'robert.m@example.com', 'phone': '9012345678'},
            {'first_name': 'Jennifer', 'last_name': 'Taylor', 'email': 'jennifer.t@example.com', 'phone': '0123456789'},
        ]

        # Vendor data
        vendors_data = [
            {'first_name': 'Mario', 'last_name': 'Rossi', 'email': 'mario.rossi@pizzahut.com', 'phone': '1112223333'},
            {'first_name': 'Wang', 'last_name': 'Chen', 'email': 'wang.chen@asianfusion.com', 'phone': '2223334444'},
            {'first_name': 'Ahmed', 'last_name': 'Hassan', 'email': 'ahmed@kebabhouse.com', 'phone': '3334445555'},
            {'first_name': 'Carlos', 'last_name': 'Garcia', 'email': 'carlos@burritobowl.com', 'phone': '4445556666'},
            {'first_name': 'Yuki', 'last_name': 'Tanaka', 'email': 'yuki@sushiworld.com', 'phone': '5556667777'},
        ]

        self.customers = []
        for data in customers_data:
            username = f"{data['first_name'].lower()}.{data['last_name'].lower()}"
            user = User.objects.create_user(
                first_name=data['first_name'],
                last_name=data['last_name'],
                username=username,
                email=data['email'],
                password='customer123'
            )
            user.role = User.CUSTOMER
            user.phone_number = data['phone']
            user.is_active = True
            user.save()
            self.customers.append(user)

            # Update user profile for customer (created automatically by signal)
            profile = UserProfile.objects.get(user=user)
            profile.address = f"{random.randint(100, 999)} Main Street"
            profile.country = "USA"
            profile.state = "California"
            profile.city = "San Francisco"
            profile.pin_code = f"{random.randint(90000, 99999)}"
            profile.latitude = str(37.7749 + random.uniform(-0.1, 0.1))
            profile.longitude = str(-122.4194 + random.uniform(-0.1, 0.1))
            profile.save()

        self.vendor_users = []
        for data in vendors_data:
            username = f"{data['first_name'].lower()}.{data['last_name'].lower()}"
            user = User.objects.create_user(
                first_name=data['first_name'],
                last_name=data['last_name'],
                username=username,
                email=data['email'],
                password='vendor123'
            )
            user.role = User.VENDOR
            user.phone_number = data['phone']
            user.is_active = True
            user.save()
            self.vendor_users.append(user)

        self.stdout.write(self.style.SUCCESS(f'✅ Created {len(self.customers)} customers and {len(self.vendor_users)} vendor users'))

    def seed_vendors(self):
        """Create vendor restaurants"""
        self.stdout.write('Creating vendors...')

        vendor_data = [
            {
                'name': 'Italian Pizza House',
                'profile_pic': 'profile-picture-1.PNG',
                'cover_photo': 'cover-photo-1.PNG',
                'address': '123 Pizza Street',
                'city': 'San Francisco',
                'state': 'California',
                'country': 'USA',
                'pin_code': '94102',
                'latitude': '37.7849',
                'longitude': '-122.4094',
            },
            {
                'name': 'Asian Fusion Delight',
                'profile_pic': 'profile-picture-2.PNG',
                'cover_photo': 'cover-photo-2.PNG',
                'address': '456 Wok Avenue',
                'city': 'San Francisco',
                'state': 'California',
                'country': 'USA',
                'pin_code': '94103',
                'latitude': '37.7749',
                'longitude': '-122.4194',
            },
            {
                'name': 'Mediterranean Kebab House',
                'profile_pic': 'profile-picture-3.PNG',
                'cover_photo': 'cover-photo-3.PNG',
                'address': '789 Spice Road',
                'city': 'San Francisco',
                'state': 'California',
                'country': 'USA',
                'pin_code': '94104',
                'latitude': '37.7949',
                'longitude': '-122.3994',
            },
            {
                'name': 'Mexican Burrito Bowl',
                'profile_pic': 'profile-picture-4.PNG',
                'cover_photo': 'cover-photo-4.PNG',
                'address': '321 Taco Lane',
                'city': 'San Francisco',
                'state': 'California',
                'country': 'USA',
                'pin_code': '94105',
                'latitude': '37.7649',
                'longitude': '-122.4294',
            },
            {
                'name': 'Sushi World',
                'profile_pic': 'profile-picture-5.PNG',
                'cover_photo': 'cover-photo-5.PNG',
                'address': '654 Sashimi Boulevard',
                'city': 'San Francisco',
                'state': 'California',
                'country': 'USA',
                'pin_code': '94106',
                'latitude': '37.7549',
                'longitude': '-122.4394',
            },
        ]

        self.vendors = []
        for i, data in enumerate(vendor_data):
            user = self.vendor_users[i]

            # Update user profile with images (created automatically by signal)
            profile_pic_path = os.path.join(settings.BASE_DIR, 'dishonline_main', 'static', 'extra-images', data['profile_pic'])
            cover_photo_path = os.path.join(settings.BASE_DIR, 'dishonline_main', 'static', 'extra-images', data['cover_photo'])

            user_profile = UserProfile.objects.get(user=user)
            user_profile.address = data['address']
            user_profile.country = data['country']
            user_profile.state = data['state']
            user_profile.city = data['city']
            user_profile.pin_code = data['pin_code']
            user_profile.latitude = data['latitude']
            user_profile.longitude = data['longitude']
            user_profile.save()

            # Copy profile and cover images if they exist
            if os.path.exists(profile_pic_path):
                with open(profile_pic_path, 'rb') as f:
                    user_profile.profile_picture.save(data['profile_pic'], File(f), save=True)

            if os.path.exists(cover_photo_path):
                with open(cover_photo_path, 'rb') as f:
                    user_profile.cover_photo.save(data['cover_photo'], File(f), save=True)

            # Create vendor license dummy file
            license_path = os.path.join(settings.BASE_DIR, 'dishonline_main', 'static', 'extra-images', 'listing-logo18.png')

            vendor = Vendor.objects.create(
                user=user,
                user_profile=user_profile,
                vendor_name=data['name'],
                vendor_slug=slugify(data['name']),
                is_approved=True
            )

            if os.path.exists(license_path):
                with open(license_path, 'rb') as f:
                    vendor.vendor_license.save(f'license_{vendor.id}.png', File(f), save=True)

            self.vendors.append(vendor)

        self.stdout.write(self.style.SUCCESS(f'✅ Created {len(self.vendors)} vendors'))

    def seed_categories(self):
        """Create food categories for each vendor"""
        self.stdout.write('Creating categories...')

        category_templates = [
            {'name': 'Pizza', 'description': 'Delicious handmade pizzas with fresh ingredients'},
            {'name': 'Burgers', 'description': 'Juicy burgers made from premium beef'},
            {'name': 'Chicken', 'description': 'Tender chicken dishes in various styles'},
            {'name': 'Seafood', 'description': 'Fresh seafood from the ocean'},
            {'name': 'Rice Bowls', 'description': 'Healthy and filling rice bowl meals'},
            {'name': 'Vegetarian', 'description': 'Plant-based delicious meals'},
            {'name': 'Beverages', 'description': 'Refreshing drinks and smoothies'},
            {'name': 'Desserts', 'description': 'Sweet treats to end your meal'},
        ]

        self.categories = {}
        count = 0

        for vendor in self.vendors:
            self.categories[vendor.id] = []
            # Each vendor gets 4-6 random categories
            num_categories = random.randint(4, 6)
            selected_categories = random.sample(category_templates, num_categories)

            for cat_data in selected_categories:
                category = Category.objects.create(
                    vendor=vendor,
                    category_name=cat_data['name'],
                    slug=f"{slugify(cat_data['name'])}-{vendor.id}",
                    description=cat_data['description']
                )
                self.categories[vendor.id].append(category)
                count += 1

        self.stdout.write(self.style.SUCCESS(f'✅ Created {count} categories'))

    def seed_food_items(self):
        """Create food items with images"""
        self.stdout.write('Creating food items...')

        # Map food images to their categories and details
        food_items_data = [
            # Pizza
            {'category': 'Pizza', 'name': 'Italian Classic Pizza', 'image': 'italian-pizza-600x600.jpg',
             'description': 'Traditional Italian pizza with mozzarella, tomatoes, and basil', 'price': (12.99, 18.99)},
            {'category': 'Pizza', 'name': 'Vegetarian Pizza', 'image': 'veg-pizza-600x600.jpg',
             'description': 'Loaded with fresh vegetables and cheese', 'price': (11.99, 16.99)},
            {'category': 'Pizza', 'name': 'Margherita Pizza', 'image': 'pizza-600x600.jpg',
             'description': 'Classic Margherita with fresh mozzarella', 'price': (10.99, 15.99)},

            # Burgers
            {'category': 'Burgers', 'name': 'Classic Beef Burger', 'image': 'burger-600x600.jpg',
             'description': 'Juicy beef patty with lettuce, tomato, and special sauce', 'price': (8.99, 12.99)},

            # Chicken
            {'category': 'Chicken', 'name': 'Grilled Chicken Breast', 'image': 'chicken-600x600.jpg',
             'description': 'Perfectly grilled chicken breast with herbs', 'price': (13.99, 17.99)},
            {'category': 'Chicken', 'name': 'Pan-Fried Chicken', 'image': 'Pan-Fried-Chicken-600x600.jpg',
             'description': 'Crispy pan-fried chicken with golden crust', 'price': (11.99, 15.99)},
            {'category': 'Chicken', 'name': 'Chicken BBQ', 'image': 'chicken-barbeque.jpg',
             'description': 'Smoky barbecue chicken with tangy sauce', 'price': (14.99, 18.99)},

            # Seafood
            {'category': 'Seafood', 'name': 'Seafood Platter', 'image': 'seafood-600x600.jpg',
             'description': 'Mixed seafood with prawns, fish, and calamari', 'price': (19.99, 25.99)},
            {'category': 'Seafood', 'name': 'Grilled Tuna Fish', 'image': 'tuna-fish.jpg',
             'description': 'Fresh grilled tuna steak', 'price': (16.99, 21.99)},

            # Rice Bowls
            {'category': 'Rice Bowls', 'name': 'Steamed Rice Bowl', 'image': 'steam-rice.jpg',
             'description': 'Fluffy steamed rice with vegetables', 'price': (7.99, 10.99)},
            {'category': 'Rice Bowls', 'name': 'Asian Rice Bowl', 'image': 'rice-bowl.jpg',
             'description': 'Rice bowl with chicken, vegetables, and teriyaki sauce', 'price': (12.99, 16.99)},
        ]

        count = 0
        for vendor in self.vendors:
            vendor_categories = self.categories[vendor.id]

            for category in vendor_categories:
                # Find matching food items for this category
                matching_items = [item for item in food_items_data if item['category'] == category.category_name]

                if not matching_items:
                    # If no matching items, create generic ones
                    for j in range(random.randint(2, 4)):
                        price = Decimal(str(random.uniform(8.99, 24.99))).quantize(Decimal('0.01'))
                        FoodItem.objects.create(
                            vendor=vendor,
                            category=category,
                            food_title=f"{category.category_name} Special {j+1}",
                            slug=f"{slugify(category.category_name)}-special-{j+1}-{vendor.id}",
                            description=f"Delicious {category.category_name.lower()} dish",
                            price=price,
                            is_available=True
                        )
                        count += 1
                else:
                    # Create items with actual images
                    items_to_add = random.sample(matching_items, min(len(matching_items), random.randint(2, 4)))

                    for item_data in items_to_add:
                        price_range = item_data['price']
                        price = Decimal(str(random.uniform(price_range[0], price_range[1]))).quantize(Decimal('0.01'))

                        food_item = FoodItem.objects.create(
                            vendor=vendor,
                            category=category,
                            food_title=item_data['name'],
                            slug=f"{slugify(item_data['name'])}-{vendor.id}-{count}",
                            description=item_data['description'],
                            price=price,
                            is_available=random.choice([True, True, True, False])  # 75% available
                        )

                        # Add image
                        image_path = os.path.join(settings.BASE_DIR, 'dishonline_main', 'static', 'extra-images', item_data['image'])
                        if os.path.exists(image_path):
                            with open(image_path, 'rb') as f:
                                food_item.image.save(item_data['image'], File(f), save=True)

                        count += 1

        self.stdout.write(self.style.SUCCESS(f'✅ Created {count} food items'))

    def seed_opening_hours(self):
        """Create opening hours for vendors"""
        self.stdout.write('Creating opening hours...')

        count = 0
        for vendor in self.vendors:
            # Most restaurants are open Mon-Sun
            for day in range(1, 8):  # 1=Monday to 7=Sunday
                if day == 7 and random.random() < 0.3:  # 30% closed on Sunday
                    OpeningHour.objects.create(
                        vendor=vendor,
                        day=day,
                        is_closed=True
                    )
                else:
                    # Morning shift
                    OpeningHour.objects.create(
                        vendor=vendor,
                        day=day,
                        from_hour='09:00 AM',
                        to_hour='03:00 PM',
                        is_closed=False
                    )
                    # Evening shift
                    OpeningHour.objects.create(
                        vendor=vendor,
                        day=day,
                        from_hour='05:00 PM',
                        to_hour='11:00 PM',
                        is_closed=False
                    )
                    count += 2

        self.stdout.write(self.style.SUCCESS(f'✅ Created {count} opening hours'))

    def seed_orders(self):
        """Create sample orders"""
        self.stdout.write('Creating orders...')

        payment_methods = ['Stripe', 'SSLCommerz']
        statuses = ['New', 'Accepted', 'Completed', 'Cancelled']

        count = 0
        for customer in self.customers[:7]:  # First 7 customers place orders
            num_orders = random.randint(1, 4)

            for _ in range(num_orders):
                # Create payment
                payment = Payment.objects.create(
                    user=customer,
                    transaction_id=f'TXN{random.randint(100000, 999999)}',
                    payment_method=random.choice(payment_methods),
                    amount=str(random.randint(20, 100)),
                    status='Completed'
                )

                # Get customer profile
                customer_profile = UserProfile.objects.get(user=customer)

                # Create order
                order = Order.objects.create(
                    user=customer,
                    payment=payment,
                    order_number='TEMP',  # Temporary, will be generated after save
                    first_name=customer.first_name,
                    last_name=customer.last_name,
                    phone=customer.phone_number,
                    email=customer.email,
                    address=customer_profile.address,
                    country=customer_profile.country,
                    state=customer_profile.state,
                    city=customer_profile.city,
                    pin_code=customer_profile.pin_code,
                    total=0,  # Will calculate
                    total_tax=0,
                    payment_method=payment.payment_method,
                    status=random.choice(statuses),
                    is_ordered=True
                )

                # Generate proper order number using order ID
                order.order_number = generate_order_number(order.id)
                order.save()

                # Add items from 1-2 random vendors
                selected_vendors = random.sample(self.vendors, random.randint(1, 2))
                order.vendors.set(selected_vendors)

                total_amount = 0
                for vendor in selected_vendors:
                    # Get random food items from this vendor
                    vendor_items = FoodItem.objects.filter(vendor=vendor, is_available=True)
                    if vendor_items.exists():
                        num_items = random.randint(1, 4)
                        selected_items = random.sample(list(vendor_items), min(num_items, vendor_items.count()))

                        for food_item in selected_items:
                            quantity = random.randint(1, 3)
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

                # Update order total
                tax = total_amount * 0.1  # 10% tax
                order.total = total_amount
                order.total_tax = tax
                order.save()

                count += 1

        self.stdout.write(self.style.SUCCESS(f'✅ Created {count} orders'))

    def seed_reviews(self):
        """Create reviews for food items"""
        self.stdout.write('Creating reviews...')

        review_texts = [
            "Absolutely delicious! Will order again.",
            "Great taste and generous portions.",
            "Food arrived hot and fresh. Highly recommend!",
            "Average taste, nothing special.",
            "Best meal I've had in a while!",
            "Good food but a bit pricey.",
            "Fresh ingredients and well prepared.",
            "Disappointed with the portion size.",
            "Amazing flavors! Worth every penny.",
            "Decent food, quick delivery.",
        ]

        count = 0
        # Create reviews from customers who have ordered
        completed_orders = Order.objects.filter(status='Completed')

        for order in completed_orders:
            ordered_foods = OrderedFood.objects.filter(order=order)

            # Review 50-80% of ordered items
            items_to_review = random.sample(
                list(ordered_foods),
                random.randint(max(1, len(ordered_foods) // 2), len(ordered_foods))
            )

            for ordered_food in items_to_review:
                if not Review.objects.filter(user=order.user, fooditem=ordered_food.fooditem, order=order).exists():
                    Review.objects.create(
                        user=order.user,
                        fooditem=ordered_food.fooditem,
                        order=order,
                        rating=random.randint(3, 5),  # Mostly positive reviews
                        review_text=random.choice(review_texts)
                    )
                    count += 1

        self.stdout.write(self.style.SUCCESS(f'✅ Created {count} reviews'))

    def seed_user_activities(self):
        """Create user activity logs"""
        self.stdout.write('Creating user activities...')

        search_queries = [
            'pizza', 'burger', 'chicken', 'sushi', 'pasta',
            'seafood', 'vegetarian', 'dessert', 'italian', 'chinese'
        ]

        count = 0
        for customer in self.customers:
            # Add search activities
            for _ in range(random.randint(3, 8)):
                UserActivity.objects.create(
                    user=customer,
                    activity_type='search',
                    search_query=random.choice(search_queries),
                    created_at=datetime.now() - timedelta(days=random.randint(1, 30))
                )
                count += 1

            # Add view activities
            viewed_items = random.sample(
                list(FoodItem.objects.all()),
                min(random.randint(10, 20), FoodItem.objects.count())
            )
            for item in viewed_items:
                UserActivity.objects.create(
                    user=customer,
                    fooditem=item,
                    vendor=item.vendor,
                    activity_type='view',
                    created_at=datetime.now() - timedelta(days=random.randint(1, 30))
                )
                count += 1

            # Add cart activities
            cart_items = random.sample(
                list(FoodItem.objects.all()),
                min(random.randint(3, 8), FoodItem.objects.count())
            )
            for item in cart_items:
                UserActivity.objects.create(
                    user=customer,
                    fooditem=item,
                    vendor=item.vendor,
                    activity_type='cart',
                    created_at=datetime.now() - timedelta(days=random.randint(1, 20))
                )
                count += 1

            # Add order activities for completed orders
            customer_orders = OrderedFood.objects.filter(user=customer)
            for ordered_food in customer_orders:
                UserActivity.objects.create(
                    user=customer,
                    fooditem=ordered_food.fooditem,
                    vendor=ordered_food.fooditem.vendor,
                    activity_type='order',
                    created_at=ordered_food.created_at
                )
                count += 1

        self.stdout.write(self.style.SUCCESS(f'✅ Created {count} user activities'))
