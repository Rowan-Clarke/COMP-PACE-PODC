import os

# Gunicorn config variables
bind = "0.0.0.0:10000"  # Use a specific port
workers = 4
threads = 4
timeout = 120