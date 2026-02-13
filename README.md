# Django Multi-Vendor Restaurant Management System

A comprehensive multi-vendor restaurant management platform built with Django, featuring vendor management, menu creation, order processing, marketplace functionality, and an AI-powered recommendation system.

## Features

- 🏪 Multi-vendor restaurant management
- 📦 Order management and tracking
- 🗺️ Location-based services with PostGIS
- 💳 Payment gateway integration (Stripe, SSLCommerz)
- 🤖 AI-powered recommendation system
- 📱 Responsive design
- 👥 User roles (Admin, Vendor, Customer)
- 📊 Dashboard and analytics

## Tech Stack

- **Backend**: Django 4.0.3
- **Database**: PostgreSQL with PostGIS extension
- **Frontend**: HTML, CSS, JavaScript, Bootstrap
- **Payment**: Stripe, SSLCommerz
- **Maps**: Google Maps API
- **Deployment**: Docker, Gunicorn

## Prerequisites

Before you begin, ensure you have the following installed:
- Docker (version 20.10 or higher)
- Docker Compose (version 1.29 or higher)
- Git

## Quick Start with Docker

### 1. Clone the Repository

```bash
git clone <repository-url>
cd django_multivendor_restaurant_management
```

### 2. Set Up Environment Variables

Copy the example environment file and update it with your configuration:

```bash
cp .env.example .env
```

Edit the `.env` file and configure the following:

```env
# Django Settings
SECRET_KEY=your-secret-key-here  # Generate using: python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
DEBUG=True  # Set to False in production

# Database Configuration (Docker)
DB_NAME=dishonline_db
DB_USER=postgres
DB_PASSWORD=postgres123  # Change this to a strong password
DB_HOST=db

# Email Configuration (for Gmail)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password  # Use App Password, not your Gmail password

# Google Maps API
GOOGLE_API_KEY=your-google-api-key  # Get from https://console.cloud.google.com/

# Stripe Payment Gateway (Test Mode)
STRIPE_PUBLIC_KEY=pk_test_xxxxxx  # Get from https://dashboard.stripe.com/test/apikeys
STRIPE_SECRET_KEY=sk_test_xxxxxx

# SSLCommerz Payment Gateway (Sandbox)
SSLCOMMERZ_STORE_ID=your_store_id
SSLCOMMERZ_STORE_PASSWORD=your_store_password
SSLCOMMERZ_SANDBOX=True
```

