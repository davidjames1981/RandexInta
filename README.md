# Randex Integration Portal

A Django-based web application for managing and processing orders through API integration.

## Prerequisites

- Python 3.11 or higher
- Docker and Docker Compose (optional, for containerized deployment)
- Redis (required for Celery)
- SQL Server (for database)

## Local Development Setup

1. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create necessary directories:
```bash
mkdir -p Files/Completed Files/Error Files/logs
```

4. Run migrations:
```bash
python manage.py migrate
```

5. Start Redis (required for Celery):
```bash
# On Windows, you may need to install Redis separately
# On Linux/Mac, you can use your package manager
```

6. Start Celery worker and beat (in separate terminals):
```bash
# Terminal 1 - Celery worker
celery -A CompactNodeInt worker -l INFO

# Terminal 2 - Celery beat
celery -A CompactNodeInt beat -l INFO
```

7. Run the development server:
```bash
python manage.py runserver
```

8. Visit http://localhost:8000 in your browser

## Docker Deployment

1. Create necessary directories:
```bash
mkdir -p Files/Completed Files/Error Files/logs
```

2. Build and start the containers:
```bash
docker-compose up --build
```

3. Run migrations (first time only):
```bash
docker-compose exec web python manage.py migrate
```

4. Create a superuser (optional):
```bash
docker-compose exec web python manage.py createsuperuser
```

5. Access the application at http://localhost:8000

## Development vs Production

The application can be run in two modes:

### Local Development
- Uses Django's development server
- Debug mode enabled
- Direct access to local files
- Manual process management
- Uses local Redis instance
- Uses local SQL Server
- Uses `.env.local` for configuration

### Docker Deployment
- Containerized environment
- Isolated services
- Persistent volumes for data
- Automated process management
- Uses containerized Redis
- Uses host SQL Server (via host.docker.internal)
- Uses `.env.docker` for configuration

## Environment Variables

The following environment variables are required:

### Database Settings
- `DB_ENGINE`: Database engine (mssql+pyodbc)
- `DB_NAME`: Database name
- `DB_USER`: Database user
- `DB_PASSWORD`: Database password
- `DB_HOST`: Database host (localhost for local, host.docker.internal for Docker)
- `DB_PORT`: Database port

### Redis Settings
- `REDIS_HOST`: Redis host (localhost for local, redis for Docker)
- `REDIS_PORT`: Redis port

### File Paths
- `WATCH_FOLDER`: Directory to watch for new files
- `COMPLETED_FOLDER`: Directory for processed files
- `ERROR_FOLDER`: Directory for files with errors
- `LOG_FOLDER`: Directory for log files

### API Settings
- `API_HOST`: API endpoint URL
- `WAREHOUSE`: Warehouse identifier

### Task Frequency Settings
- `IMPORT_FREQUENCY`: Excel import check interval (seconds)
- `API_FREQUENCY`: API order creation interval (seconds)
- `PICK_CHECK_FREQUENCY`: Pick status check interval (seconds)

### Django Settings
- `SECRET_KEY`: Django secret key
- `DEBUG`: Enable/disable debug mode

## File Structure

```
.
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.local
├── .env.docker
├── CompactNodeInt/
│   ├── settings.py
│   ├── urls.py
│   └── celery.py
└── Portal/
    ├── models.py
    ├── views.py
    ├── tasks/
    └── templates/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 