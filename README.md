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

### 3. Build and Run with Docker

```bash
# Build and start all services
docker-compose up --build

# Or run in detached mode (background)
docker-compose up -d --build
```

The application will be available at:
- **Application**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin

### 4. Create a Superuser (Optional)

A default superuser is created automatically:
- **Username**: admin
- **Password**: admin

To create a custom superuser:

```bash
docker-compose exec web python manage.py createsuperuser
```

### 5. Access the Application

Visit http://localhost:8000 in your browser.

Default admin credentials:
- **Username**: arifulislam
- **Password**: arifulislam

## Docker Commands

### Start the Application

```bash
docker-compose up
```

### Stop the Application

```bash
docker-compose down
```

### Stop and Remove Volumes (Clear Database)

```bash
docker-compose down -v
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f web
docker-compose logs -f db
```

### Run Django Commands

```bash
# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Collect static files
docker-compose exec web python manage.py collectstatic

# Access Django shell
docker-compose exec web python manage.py shell
```

### Access Database

```bash
docker-compose exec db psql -U postgres -d dishonline_db
```

### Rebuild After Code Changes

```bash
docker-compose up --build
```

## Manual Installation (Without Docker)

If you prefer to run the application without Docker:

### 1. Install PostgreSQL with PostGIS

```bash
# Ubuntu/Debian
sudo apt-get install postgresql postgresql-contrib postgis

# macOS
brew install postgresql postgis
```

### 2. Create Database

```bash
sudo -u postgres psql
CREATE DATABASE dishonline_db;
CREATE USER postgres WITH PASSWORD 'your_password';
ALTER ROLE postgres SET client_encoding TO 'utf8';
ALTER ROLE postgres SET default_transaction_isolation TO 'read committed';
ALTER ROLE postgres SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE dishonline_db TO postgres;
\c dishonline_db
CREATE EXTENSION postgis;
\q
```

### 3. Install Python Dependencies

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Configure Environment

Update `.env` file with your database host (localhost) and credentials.

### 5. Run Migrations

```bash
python manage.py migrate
```

### 6. Create Superuser

```bash
python manage.py createsuperuser
```

### 7. Run Development Server

```bash
python manage.py runserver
```

## Project Structure

```
├── accounts/              # User authentication and profiles
├── customers/             # Customer management
├── dishonline_main/       # Main project settings
├── marketplace/           # Marketplace functionality
├── menu/                  # Menu and food items management
├── orders/                # Order processing
├── recommendations/       # AI recommendation engine
├── vendor/                # Vendor management
├── templates/             # HTML templates
├── static/                # Static files (CSS, JS, images)
├── media/                 # User-uploaded files
├── Dockerfile             # Docker configuration
├── docker-compose.yml     # Docker Compose configuration
├── docker-entrypoint.sh   # Docker startup script
└── requirements.txt       # Python dependencies
```

## Configuration Notes

### Google Maps API
To use location features:
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project and enable Maps JavaScript API
3. Get your API key and add it to `.env`

### Email Configuration
For Gmail:
1. Enable 2-factor authentication
2. Generate an App Password
3. Use the App Password in your `.env` file

### Payment Gateways

**Stripe** (for international payments):
1. Sign up at [Stripe](https://stripe.com)
2. Get test API keys from dashboard
3. Add to `.env` file

**SSLCommerz** (for Bangladesh):
1. Sign up at [SSLCommerz](https://www.sslcommerz.com/)
2. Get sandbox credentials
3. Add to `.env` file

## Troubleshooting

### Port Already in Use

If port 8000 or 5432 is already in use:

```bash
# Change the port in docker-compose.yml
ports:
  - "8001:8000"  # Use 8001 instead of 8000
```

### Database Connection Issues

```bash
# Check if database is running
docker-compose ps

# Restart database service
docker-compose restart db

# Check database logs
docker-compose logs db
```

### Migration Issues

```bash
# Reset migrations (WARNING: This will delete all data)
docker-compose down -v
docker-compose up --build
```

### Static Files Not Loading

```bash
docker-compose exec web python manage.py collectstatic --noinput
```

## Production Deployment

For production deployment:

1. Set `DEBUG=False` in `.env`
2. Update `ALLOWED_HOSTS` in settings.py
3. Use strong `SECRET_KEY`
4. Use environment-specific database credentials
5. Configure proper SSL certificates
6. Use a reverse proxy (Nginx)
7. Set up proper backup strategies

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
- Create an issue in the repository
- Contact: django.dishonline@gmail.com

## Default Credentials

**Admin Panel**:
- Username: arifulislam
- Password: arifulislam

**Docker Default Superuser** (if auto-created):
- Username: admin
- Password: admin

Remember to change these credentials in production!