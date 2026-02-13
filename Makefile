.PHONY: help build up down restart logs shell migrate createsuperuser collectstatic clean

help:
	@echo "Django Multi-Vendor Restaurant Management - Docker Commands"
	@echo ""
	@echo "Available commands:"
	@echo "  make build          - Build Docker images"
	@echo "  make up             - Start all services"
	@echo "  make down           - Stop all services"
	@echo "  make restart        - Restart all services"
	@echo "  make logs           - View logs from all services"
	@echo "  make logs-web       - View web application logs"
	@echo "  make logs-db        - View database logs"
	@echo "  make shell          - Access Django shell"
	@echo "  make bash           - Access container bash"
	@echo "  make migrate        - Run database migrations"
	@echo "  make makemigrations - Create new migrations"
	@echo "  make createsuperuser - Create Django superuser"
	@echo "  make collectstatic  - Collect static files"
	@echo "  make clean          - Stop and remove all containers, volumes, and images"
	@echo "  make test           - Run tests"
	@echo "  make db-shell       - Access PostgreSQL shell"

build:
	docker-compose build

up:
	docker-compose up

up-d:
	docker-compose up -d

down:
	docker-compose down

restart:
	docker-compose restart

logs:
	docker-compose logs -f

logs-web:
	docker-compose logs -f web

logs-db:
	docker-compose logs -f db

shell:
	docker-compose exec web python manage.py shell

bash:
	docker-compose exec web /bin/bash

migrate:
	docker-compose exec web python manage.py migrate

makemigrations:
	docker-compose exec web python manage.py makemigrations

createsuperuser:
	docker-compose exec web python manage.py createsuperuser

collectstatic:
	docker-compose exec web python manage.py collectstatic --noinput

clean:
	docker-compose down -v --rmi all

test:
	docker-compose exec web python manage.py test

db-shell:
	docker-compose exec db psql -U postgres -d dishonline_db
