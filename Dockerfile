FROM python:3.13-alpine

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install dependencies
RUN apk add --no-cache \
    postgresql-client \
    libpq \
    gcc \
    musl-dev \
    postgresql-dev \
    netcat-openbsd

# Create non-root user
RUN addgroup -S app && adduser -S -G app app

WORKDIR /app

# Install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY --chown=app:app . .
RUN chmod +x entrypoint.sh

USER app

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
CMD ["gunicorn", "faberorg.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
