# Use slim Python and install mysql client build deps
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /code

# system deps (include pkg-config)
RUN apt-get update && apt-get install -y \
    build-essential default-libmysqlclient-dev libssl-dev libjpeg-dev zlib1g-dev pkg-config \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel \
 && pip install --no-cache-dir -r requirements.txt

COPY . .

# Collect static if you use it
# RUN python manage.py collectstatic --noinput

CMD ["gunicorn", "proj1.wsgi:application", "--bind", "0.0.0.0:8000"]