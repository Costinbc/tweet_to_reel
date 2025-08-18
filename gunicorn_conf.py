import os

PORT = os.getenv("PORT", "8080")
wsgi_app = "src.app:app"
chdir = "/app"

bind = f"0.0.0.0:{PORT}"
workers = 1
worker_class = "gthread"
threads = 8

timeout = 0
graceful_timeout = 30
accesslog = "-"
errorlog = "-"
loglevel = "info"