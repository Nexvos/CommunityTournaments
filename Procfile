web: daphne CommunityTournaments.asgi:application --port $PORT --bind 0.0.0.0 -v2
worker: python manage.py runworker channels -v2
worker: celery worker --app=CommunityTournaments.celery.app