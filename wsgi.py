"""WSGI entry point for Gunicorn:
gunicorn --bind 127.0.0.1:8000 --workers 2 --threads 2 wsgi:app
"""
from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)