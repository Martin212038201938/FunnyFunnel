"""WSGI entry point for production deployment (e.g., AlwaysData)."""

from dotenv import load_dotenv
load_dotenv()

from app import create_app

application = create_app()

# For gunicorn: gunicorn wsgi:application
