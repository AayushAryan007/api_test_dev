# proj1 — Django Book CRUD (Docker + MySQL migration)

Short
- Django REST + JWT auth project with a Book model and CRUD endpoints.
- Originally used SQLite (db.sqlite3). Migrated data to a MySQL container and dockerized the app with docker-compose.

Tech stack
- Python 3.12, Django 6.x, Django REST Framework, djangorestframework-simplejwt
- MySQL 8.0 (container)
- Gunicorn (WSGI)
- Docker, Docker Compose
- SQLite (legacy, source data) → MySQL (production dev)

Repository layout (important files)
- proj1/                 — Django project root
  - manage.py
  - proj1/settings.py
  - proj1/wsgi.py
  - proj1/__init__.py  (optional PyMySQL shim)
  - account/            — Book model, serializers, views
  - media/              — uploaded files (mounted volume)
  - Dockerfile
  - docker-compose.yml
  - requirements.txt
  - db.sqlite3 (local backup; ignored by .gitignore)

Prerequisites (local)
- Docker Desktop (macOS) running
- (Optional) Homebrew + mysql-client for local MySQL CLI:
  brew install mysql-client
- Python virtualenv if running locally (venv/activate)

Quick start — docker (recommended)
1. Build web image:
   docker compose build --no-cache web

2. Start DB only and wait:
   docker compose up --detach db
   docker compose logs -f db

3. Apply migrations on MySQL:
   docker compose run --rm web python manage.py migrate

4. Load data dumped from SQLite (if available):
   docker compose run --rm web python manage.py loaddata data.json

5. Restore media (local):
   tar -xzf media.tar.gz -C ./media

6. Start web:
   docker compose up --detach web

7. Tail logs:
   docker compose logs -f web

Stop & cleanup:
- docker compose down -v

How the SQLite → MySQL migration was done
1. Backup SQLite & media:
   python manage.py dumpdata --natural-foreign --natural-primary --exclude auth.permission --exclude contenttypes > data.json
   tar -czf media.tar.gz media/

2. Start MySQL (docker compose up --detach db) and run migrations against it:
   docker compose run --rm web python manage.py migrate

3. Load data into MySQL:
   docker compose run --rm web python manage.py loaddata data.json

4. Restore media into ./media (mounted as a volume for the web container).

Database connection details (docker-compose)
- DB_HOST: db
- DB_NAME: proj1
- DB_USER: proj1user
- DB_PASS: proj1pass
- DB_PORT: 3306
- MySQL root password (for db container): rootpass

Connect with MySQL client (from host)
- Using mysql client (brew):
  mysql -h 127.0.0.1 -P 3306 -u proj1user -pproj1pass -e "USE proj1; SHOW TABLES;"

- Inside container:
  docker compose exec db mysql -u root -prootpass -e "USE proj1; SHOW TABLES;"

Driver notes: mysqlclient vs PyMySQL
- If `pip install mysqlclient` fails locally (pkg-config / build deps), options:
  - Install native deps on macOS:
    brew install pkg-config mysql-client openssl
    export LDFLAGS/CPPFLAGS/PKG_CONFIG_PATH accordingly, then pip install mysqlclient
  - Or use PyMySQL (no native compile). Add shim:
    proj1/proj1/__init__.py:
    import pymysql
    pymysql.install_as_MySQLdb()
  - The web container installs system libs in Dockerfile; ensure Dockerfile includes the required apt packages if using mysqlclient.

Common build/run issues & fixes
- DNS failures during apt-get in build: restart Docker Desktop, configure Docker daemon DNS (e.g. 8.8.8.8), or build with network host if applicable.
- Django vs Python mismatch: use python:3.12-slim base when using Django 6.x.
- docker compose version warning: remove top-level `version:` key or ignore (Compose V2).

Important commands (summary)
- Build web: docker compose build --no-cache web
- Start DB: docker compose up --detach db
- Migrate: docker compose run --rm web python manage.py migrate
- Load data: docker compose run --rm web python manage.py loaddata data.json
- Start web: docker compose up --detach web
- Show DB tables: docker compose exec db mysql -u root -prootpass -e "USE proj1; SHOW TABLES;"

JWT & API
- JWT auth implemented using rest_framework_simplejwt and a cookie-based auth class at account.auth.CookieJWTAuthentication.
- Test endpoints with HTTP client (Postman/curl). Ensure token flow works after DB migration.

Notes & best practices
- Keep db.sqlite3 as a backup until migration fully validated.
- Ensure media files are persisted via a Docker volume or host mount.
- Remove secret keys / passwords from version control for production; use secrets manager or env files.

If you want, I can:
- Generate a polished README with badges and license.
- Create a .env.example and update settings.py to read env vars using python-dotenv.
