FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=evoicebot.settings

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc python3-dev \
    && pip install -r requirements.txt \
    && pip install gunicorn \
    && apt-get purge -y --auto-remove gcc python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy project
COPY . .

# Expose port
EXPOSE 8000

# Run application with Gunicorn WSGI server
CMD ["python", "-m", "gunicorn", "evoicebot.wsgi:application", "--bind", "0.0.0.0:8000"]