# Django Bulk Book Upload API with Async Task Queue

A production-ready Django REST API for bulk uploading book data via CSV with real-time status tracking using Celery background workers and Redis task queue.

## 📋 Table of Contents
- [Project Overview](#project-overview)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Setup & Installation](#setup--installation)
- [API Endpoints](#api-endpoints)
- [Usage Guide](#usage-guide)
- [Project Structure](#project-structure)
- [How It Works](#how-it-works)
- [Testing](#testing)

---

## 🎯 Project Overview

**Purpose:** Allow users to bulk upload book data (CSV format) asynchronously, with each row processed with a configurable delay (0.5s default) and tracked via unique task IDs.

**Key Features:**
- ✅ CSV bulk upload with per-row 0.5s processing delay
- ✅ JWT-based authentication (Postman/API-friendly)
- ✅ Real-time task status tracking (pending/processing/success/failed)
- ✅ Batch status aggregation (see all tasks in one upload)
- ✅ Automatic retry on failure (up to 3 retries)
- ✅ Non-blocking async processing (user gets response instantly)
- ✅ Dockerized full stack (MySQL, Redis, Django, Celery)
- ✅ Persistent task records (survives worker crashes)

---

## 🛠️ Tech Stack

| Component | Purpose | Version |
|-----------|---------|---------|
| **Django** | Web framework & REST API | 6.0 |
| **Django REST Framework** | API serialization & views | Latest |
| **djangorestframework-simplejwt** | JWT authentication | Latest |
| **Celery** | Async task queue | 5.6.2 |
| **Redis** | Message broker & result backend | 7.0 |
| **MySQL** | Database (user, book, task records) | 8.0 |
| **PyMySQL** | MySQL driver (with cryptography for auth) | Latest |
| **Gunicorn** | WSGI server | Latest |
| **Docker & Docker Compose** | Containerization & orchestration | Latest |
| **Colima** | Docker runtime (macOS alternative to Docker Desktop) | Latest |

---

## 🏗️ Architecture

### System Flow Diagram
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            User (Postman/API Client)                        │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                    POST /signup/ (create account)
                    POST /login/  (get JWT token)
                                 │
                                 ▼
                    ┌────────────────────────────┐
                    │  Django Web Server         │
                    │  (Gunicorn, port 8000)     │
                    │  ├─ Auth APIs              │
                    │  ├─ Book CRUD APIs         │
                    │  └─ Bulk Upload API        │
                    └────────────┬───────────────┘
                                 │
                    POST /bulk-upload/ (CSV file)
                                 │
                                 ▼
                    ┌────────────────────────────┐
                    │  BulkUploadBooksAPIView    │
                    │  1. Parse CSV              │
                    │  2. Create BulkUploadTask  │
                    │     records (status=pending)
                    │  3. Enqueue Celery tasks   │
                    │     to Redis Queue         │
                    │  4. Return batch_id (HTTP 202)
                    └────────────┬───────────────┘
                                 │
                                 ▼
                    ┌────────────────────────────┐
                    │   Redis Queue              │
                    │   (Message Broker)         │
                    │                            │
                    │   [Task1]  [Task2]  [Task3]│
                    └────┬───────┬───────┬───────┘
                         │       │       │
         ┌───────────────┼───────┼───────┼──────────────┐
         │               │       │       │              │
         ▼               ▼       ▼       ▼              ▼
    ┌─────────┐     ┌─────────┐  ┌──────────┐    ┌──────────┐
    │ Celery  │     │ Celery  │  │ Celery   │    │ Celery   │
    │ Worker1 │     │ Worker2 │  │ Worker3  │    │ Worker N │
    └────┬────┘     └────┬────┘  └────┬─────┘    └────┬─────┘
         │               │            │              │
         │  (for each task:)          │              │
         │  1. Sleep 0.5s             │              │
         │  2. Create Book in DB      │              │
         │  3. Update BulkUploadTask  │              │
         │     (status=success)       │              │
         │  4. Store result in Redis  │              │
         └───────────────┼────────────┼──────────────┘
                         │
                         ▼
         ┌──────────────────────────────┐
         │   MySQL Database             │
         │   ├─ auth_user               │
         │   ├─ account_book            │
         │   └─ account_bulkuploadtask  │
         └──────────────────────────────┘
         
         ┌──────────────────────────────┐
         │   Redis Results Backend      │
         │   (stores task results)      │
         └──────────────────────────────┘
         
         
User polls status:
    │
    GET /task-status/?task_id=<uuid>
    GET /batch-status/?batch_id=<uuid>
    │
    ▼
TaskStatusAPIView / BatchStatusAPIView
    │
    Query BulkUploadTask records from DB
    │
    ▼
Return current status (pending/processing/success/failed)
```

### Component Interaction
```
Django (Web)  ─────────────────► Redis Queue ────────────► Celery Workers
                 Enqueue tasks                                   │
                                                                 │
                                                    Process & Update DB
                                                                 │
                                                                 ▼
User                           ◄─── TaskStatusAPIView ◄─── BulkUploadTask (DB)
    │                               / BatchStatusAPIView
    │
    └─ Poll Status (HTTP GET)
```

---

## ⚙️ Setup & Installation

### Prerequisites
- macOS with Colima installed (`brew install colima docker docker-compose`)
- Python 3.12+
- MySQL 8.0 (via Docker)

### 1. Clone & Install Dependencies
```bash
cd /Users/aayusharyan/Desktop/code/learn/Django/proj1
python -m venv env
source env/bin/activate
pip install -r requirements.txt
```

### 2. Start Colima
```bash
colima start --cpu 4 --memory 6 --disk 60
```

### 3. Build & Start Docker Services
```bash
docker compose build --no-cache web
docker compose up --detach db redis web celery_worker
```

### 4. Run Migrations
```bash
docker compose run --rm web python manage.py migrate
```

### 5. Create Superuser (optional)
```bash
docker compose run --rm web python manage.py createsuperuser
```

### 6. Load Sample Data (optional)
```bash
docker compose run --rm web python manage.py loaddata data.json
tar -xzf media.tar.gz -C ./media
```

### 7. Verify All Services Running
```bash
docker compose ps
docker compose logs -f web celery_worker
```

---

## 📡 API Endpoints

### Authentication

#### 1. Signup
```
POST /signup/
Content-Type: application/json

{
  "username": "testuser",
  "password": "testpass123",
  "email": "test@example.com"
}

Response (201 Created):
{
  "success": true,
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user_id": 1,
  "username": "testuser"
}
```

#### 2. Login
```
POST /login/
Content-Type: application/json

{
  "username": "testuser",
  "password": "testpass123"
}

Response (200 OK):
{
  "success": true,
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user_id": 1,
  "username": "testuser"
}
```

### Books

#### 3. List All Books
```
GET /books/
Authorization: Bearer <access_token>

Response (200 OK):
[
  {
    "id": 1,
    "title": "The Great Gatsby",
    "author": "F. Scott Fitzgerald",
    "description": "A novel of the Jazz Age",
    "picture": "/media/books/gatsby.jpg",
    "picture_url": "http://localhost:8000/media/books/gatsby.jpg"
  },
  ...
]
```

#### 4. Create Book
```
POST /books/
Authorization: Bearer <access_token>
Content-Type: multipart/form-data

{
  "title": "1984",
  "author": "George Orwell",
  "description": "A dystopian novel",
  "picture": <file>
}

Response (201 Created or redirect to /books/)
```

#### 5. Get Book Detail
```
GET /books/<id>/
Authorization: Bearer <access_token>

Response (200 OK):
{
  "id": 1,
  "title": "The Great Gatsby",
  "author": "F. Scott Fitzgerald",
  "description": "A novel of the Jazz Age",
  "picture_url": "..."
}
```

#### 6. Edit Book
```
POST /books/<id>/edit/
Authorization: Bearer <access_token>
Content-Type: multipart/form-data

{
  "title": "The Great Gatsby (Updated)",
  "author": "F. Scott Fitzgerald",
  "description": "..."
}

Response (200 OK or redirect)
```

#### 7. Delete Book
```
POST /books/<id>/delete/
Authorization: Bearer <access_token>

Response (204 No Content or redirect)
```

### Bulk Upload & Task Tracking

#### 8. Bulk Upload CSV
```
POST /bulk-upload/
Authorization: Bearer <access_token>
Content-Type: multipart/form-data

{
  "file": <test_books.csv>
}

Response (202 Accepted):
{
  "batch_id": "550e8400-e29b-41d4-a716-446655440000",
  "task_ids": [
    "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "550e8400-e29b-41d4-a716-446655440001",
    "550e8400-e29b-41d4-a716-446655440002"
  ],
  "total_rows": 3
}
```

#### 9. Check Single Task Status
```
GET /task-status/?task_id=f47ac10b-58cc-4372-a567-0e02b2c3d479
Authorization: Bearer <access_token>

Response (200 OK):
{
  "task_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "status": "success",
  "title": "The Great Gatsby",
  "author": "F. Scott Fitzgerald",
  "error_message": null,
  "created_at": "2026-01-13T06:30:00Z",
  "completed_at": "2026-01-13T06:30:00.500Z"
}
```

Possible statuses: `pending`, `processing`, `success`, `failed`

#### 10. Check Batch Status (All Tasks)
```
GET /batch-status/?batch_id=550e8400-e29b-41d4-a716-446655440000
Authorization: Bearer <access_token>

Response (200 OK):
{
  "batch_id": "550e8400-e29b-41d4-a716-446655440000",
  "total": 3,
  "pending": 0,
  "processing": 0,
  "success": 3,
  "failed": 0,
  "tasks": [
    {
      "task_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
      "status": "success",
      "title": "The Great Gatsby",
      "author": "F. Scott Fitzgerald",
      "error_message": null,
      "created_at": "2026-01-13T06:30:00Z",
      "completed_at": "2026-01-13T06:30:00.500Z"
    },
    ...
  ]
}
```

---

## 📝 Usage Guide

### Step 1: Create Account & Login (in Postman)

1. **Signup**
   - POST `http://localhost:8000/signup/`
   - Body: `{"username":"u","password":"p","email":"u@example.com"}`
   - Copy `access` token

2. **Or Login** (if already have account)
   - POST `http://localhost:8000/login/`
   - Body: `{"username":"u","password":"p"}`
   - Copy `access` token

### Step 2: Prepare CSV File

Create `test_books.csv`:
```
title,author,description
The Great Gatsby,F. Scott Fitzgerald,A novel of the Jazz Age
1984,George Orwell,A dystopian novel
To Kill a Mockingbird,Harper Lee,A classic of American literature
```

### Step 3: Upload CSV

1. POST `http://localhost:8000/bulk-upload/`
2. Headers: `Authorization: Bearer <access_token>`
3. Body: form-data → file: test_books.csv
4. Response: `{"batch_id":"...", "task_ids":[...]}`

### Step 4: Monitor Progress

**Watch celery worker logs:**
```bash
docker compose logs -f celery_worker

# Output (per 0.5s delay):
[INFO] Received task: account.tasks.process_book_upload[task1]
[INFO] Task succeeded in 0.501s
[INFO] Received task: account.tasks.process_book_upload[task2]
[INFO] Task succeeded in 0.501s
...
```

**Poll task status (in Postman):**
```
GET http://localhost:8000/task-status/?task_id=<task_id>
Headers: Authorization: Bearer <token>

# Responses over time:
{"task_id":"...", "status": "pending", ...}     (first poll)
{"task_id":"...", "status": "processing", ...}  (during processing)
{"task_id":"...", "status": "success", ...}     (after 0.5s)
```

**Poll batch status:**
```
GET http://localhost:8000/batch-status/?batch_id=<batch_id>
Headers: Authorization: Bearer <token>

# Response:
{
  "batch_id": "...",
  "total": 3,
  "pending": 0,
  "processing": 0,
  "success": 3,
  "failed": 0
}
```

### Step 5: Verify Books Created

```
GET http://localhost:8000/books/
Headers: Authorization: Bearer <token>

# Response: List of all books (including newly created ones from CSV)
```

---

## 📂 Project Structure

```
proj1/
├── Dockerfile                 # Docker image definition
├── docker-compose.yml         # Multi-container orchestration
├── requirements.txt           # Python dependencies
├── manage.py                  # Django management CLI
│
├── proj1/                     # Main Django project
│   ├── settings.py            # Django configuration
│   │   ├─ INSTALLED_APPS
│   │   ├─ MIDDLEWARE
│   │   ├─ CELERY_BROKER_URL
│   │   ├─ CELERY_RESULT_BACKEND
│   │   └─ JWT settings
│   ├── urls.py                # Root URL router
│   ├── wsgi.py                # WSGI entry point (Gunicorn)
│   ├── celery.py              # Celery app initialization
│   │   └─ Connects to Redis, autodiscovers tasks
│   └── __init__.py            # PyMySQL version patch
│
├── account/                   # Django app (auth, books, bulk upload)
│   ├── models.py              # Data models
│   │   ├─ Book (id, title, author, description, picture, user)
│   │   └─ BulkUploadTask (task_id, batch_id, status, created_book_id, ...)
│   │
│   ├── views.py               # API views
│   │   ├─ LoginAPIView (JSON, CSRF-exempt, AllowAny)
│   │   ├─ SignupAPIView (JSON, CSRF-exempt, AllowAny)
│   │   ├─ BookListCreateAPIView (JWT auth)
│   │   ├─ BookDetailAPIView (JWT auth)
│   │   ├─ BookEditAPIView (JWT auth + ownership check)
│   │   ├─ BookDeleteAPIView (JWT auth + ownership check)
│   │   ├─ BulkUploadBooksAPIView (JWT auth, parse CSV, enqueue tasks)
│   │   ├─ TaskStatusAPIView (JWT auth, query single task)
│   │   └─ BatchStatusAPIView (JWT auth, query batch summary)
│   │
│   ├── tasks.py               # Celery async tasks
│   │   └─ process_book_upload(task_id, user_id)
│   │      ├─ Sleep 0.5s
│   │      ├─ Create Book in DB
│   │      ├─ Update BulkUploadTask status
│   │      └─ Retry on failure (max 3x)
│   │
│   ├── serializers.py         # DRF serializers
│   │   ├─ BookSerializer (model → JSON)
│   │   └─ BulkUploadTaskSerializer (model → JSON)
│   │
│   ├── auth.py                # Custom authentication
│   │   └─ CookieJWTAuthentication (extract JWT from cookie)
│   │
│   ├── urls.py                # App URL patterns
│   │   └─ Routes to all API views
│   │
│   └── migrations/            # Database migrations
│       ├─ Initial migrations (create tables)
│       └─ Add BulkUploadTask model
│
├── media/                     # User-uploaded files (book pictures)
│   └─ books/
│
├── templates/                 # HTML templates (optional, for web UI)
│   ├─ login.html
│   ├─ register.html
│   ├─ takebook.html
│   ├─ mybook.html
│   └─ editbook.html
│
└── test_books.csv             # Sample CSV for testing
```

---

## 🔄 How It Works (Deep Dive)

### 1. User Uploads CSV

**File:** `account/views.py` → `BulkUploadBooksAPIView.post()`

```python
def post(self, req):
    file = req.FILES.get('file')  # Get CSV from multipart/form-data
    
    # Parse CSV
    reader = csv.DictReader(StringIO(file_content))
    rows = list(reader)
    
    batch_id = str(uuid.uuid4())  # Group all tasks from this upload
    
    for row in rows:
        # 1. Create BulkUploadTask record (status='pending')
        task = BulkUploadTask.objects.create(
            task_id=uuid.uuid4(),
            batch_id=batch_id,
            title=row['title'],
            author=row['author'],
            description=row.get('description', ''),
            status='pending'
        )
        
        # 2. Enqueue Celery task to Redis
        celery_task = process_book_upload.delay(str(task.task_id), req.user.id)
        task.celery_task_id = celery_task.id
        task.save()
    
    # 3. Return immediately (HTTP 202 = processing started)
    return Response({
        'batch_id': batch_id,
        'task_ids': [...],
        'total_rows': len(rows)
    }, status=status.HTTP_202_ACCEPTED)
```

### 2. Celery Worker Processes Task

**File:** `account/tasks.py` → `process_book_upload()`

```python
@shared_task(bind=True, max_retries=3)
def process_book_upload(self, task_id_str, user_id):
    """
    Async task executed in Celery worker (separate process)
    """
    try:
        # 1. Fetch BulkUploadTask from DB
        task = BulkUploadTask.objects.get(task_id=task_id_str)
        
        # 2. Mark as processing
        task.status = 'processing'
        task.save()
        
        # 3. Sleep 0.5 seconds (simulated processing delay)
        time.sleep(0.5)
        
        # 4. Create Book entry in DB
        book = Book.objects.create(
            title=task.title,
            author=task.author,
            description=task.description,
            user_id=user_id
        )
        
        # 5. Mark BulkUploadTask as success
        task.status = 'success'
        task.created_book_id = book
        task.completed_at = timezone.now()
        task.save()
        
        # 6. Task result stored in Redis (queryable later)
        return {'task_id': str(task.task_id), 'status': 'success', 'book_id': book.id}
    
    except Exception as exc:
        # On failure: mark task as failed, retry
        task.status = 'failed'
        task.error_message = str(exc)
        task.completed_at = timezone.now()
        task.save()
        
        # Retry up to 3 times with exponential backoff
        raise self.retry(exc=exc, countdown=5)  # Retry in 5 seconds
```

### 3. User Polls Task Status

**File:** `account/views.py` → `TaskStatusAPIView.get()`

```python
def get(self, request):
    task_id = request.query_params.get('task_id')  # Get from URL ?task_id=<uuid>
    
    # Query BulkUploadTask from DB
    task = BulkUploadTask.objects.get(task_id=task_id)
    
    # Serialize and return
    serializer = BulkUploadTaskSerializer(task)
    return Response(serializer.data)
    
# Response example:
{
  "task_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "status": "success",  # Current status from DB
  "title": "The Great Gatsby",
  "author": "F. Scott Fitzgerald",
  "error_message": null,
  "created_at": "2026-01-13T06:30:00Z",
  "completed_at": "2026-01-13T06:30:00.500Z"
}
```

### 4. Data Flow Timeline

```
T=0s:     User uploads CSV (3 rows)
          → 3 BulkUploadTask records created (status='pending')
          → 3 Celery tasks enqueued to Redis
          → HTTP 202 returned to user instantly (no wait)

T=0.1s:   Celery Worker picks up Task 1
          → Status: 'processing'
          
T=0.6s:   Task 1 completes (0.5s delay + overhead)
          → Book 1 created in DB
          → Status: 'success'
          
          Celery Worker picks up Task 2
          → Status: 'processing'
          
T=1.1s:   Task 2 completes
          → Book 2 created in DB
          → Status: 'success'
          
          Celery Worker picks up Task 3
          → Status: 'processing'
          
T=1.6s:   Task 3 completes
          → Book 3 created in DB
          → Status: 'success'

User polls /task-status/?task_id=task1 at various times:
T=0.1s → {"status": "pending"}
T=0.3s → {"status": "processing"}
T=0.7s → {"status": "success", "completed_at": "..."}
```

### 5. Queue & Result Storage (Redis)

```
Redis stores two things:

1. MESSAGE QUEUE (Celery Broker):
   Queue name: "celery"
   Contents: [
     {
       "headers": {...},
       "properties": {...},
       "body": "account.tasks.process_book_upload('task-id-1', user_id=1)"
     },
     {
       "headers": {...},
       "body": "account.tasks.process_book_upload('task-id-2', user_id=1)"
     },
     ...
   ]
   
   Workers pull from this queue, process, then remove.

2. RESULT BACKEND:
   Key: "celery-task-meta-<celery_task_id>"
   Value: {
     "task_id": "...",
     "status": "SUCCESS",
     "result": {"task_id": "...", "status": "success", "book_id": 42}
   }
   
   (Optional — we mostly read from DB, not Redis results)
```

---

## 🧪 Testing

### Test in Postman

1. **Import Collection:**
   - Create new folder: "Django Bulk Upload API"
   - Add requests (see below)

2. **Set Variables:**
   - New → Environment → `base_url`: `http://localhost:8000`
   - `token`: (copy from login response)

3. **Test Sequence:**

   **Request 1: Signup**
   ```
   POST {{base_url}}/signup/
   Content-Type: application/json
   
   {"username":"testuser","password":"testpass123","email":"test@example.com"}
   ```
   Save `access` as `{{token}}`

   **Request 2: Login**
   ```
   POST {{base_url}}/login/
   Content-Type: application/json
   
   {"username":"testuser","password":"testpass123"}
   ```
   Save `access` as `{{token}}`

   **Request 3: Upload CSV**
   ```
   POST {{base_url}}/bulk-upload/
   Authorization: Bearer {{token}}
   Body: form-data → file: test_books.csv
   ```
   Save `batch_id` and first `task_id`

   **Request 4: Poll Task Status**
   ```
   GET {{base_url}}/task-status/?task_id={{task_id}}
   Authorization: Bearer {{token}}
   ```
   (Repeat every 0.5s to see status change: pending → processing → success)

   **Request 5: Poll Batch Status**
   ```
   GET {{base_url}}/batch-status/?batch_id={{batch_id}}
   Authorization: Bearer {{token}}
   ```
   (Check summary: total, pending, success, failed)

   **Request 6: List Books**
   ```
   GET {{base_url}}/books/
   Authorization: Bearer {{token}}
   ```
   (Verify 3 new books created)

### Test via Command Line

```bash
# 1. Signup
curl -X POST http://localhost:8000/signup/ \
  -H "Content-Type: application/json" \
  -d '{"username":"u","password":"p","email":"u@example.com"}'

# 2. Login (save token)
TOKEN=$(curl -s -X POST http://localhost:8000/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"u","password":"p"}' | jq -r '.access')

# 3. Upload CSV
curl -X POST http://localhost:8000/bulk-upload/ \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test_books.csv"

# 4. Poll status (repeat)
curl http://localhost:8000/batch-status/?batch_id=<batch_id> \
  -H "Authorization: Bearer $TOKEN" | jq .

# 5. List books
curl http://localhost:8000/books/ \
  -H "Authorization: Bearer $TOKEN" | jq .
```

### Monitor Celery Worker

```bash
# Watch task processing in real-time
docker compose logs -f celery_worker

# Output:
# [2026-01-13 06:30:00,000: INFO/MainProcess] Connected to redis://redis:6379/0
# [2026-01-13 06:30:01,000: INFO/Worker] Received task: account.tasks.process_book_upload[f47ac10b...]
# [2026-01-13 06:30:01,500: INFO/Worker] Task account.tasks.process_book_upload[f47ac10b...] succeeded in 0.501s
```

### Verify Data in MySQL

```bash
# List all books
docker compose exec db mysql -u root -prootpass proj1 \
  -e "SELECT * FROM account_book;"

# List all upload tasks
docker compose exec db mysql -u root -prootpass proj1 \
  -e "SELECT task_id, batch_id, status, title, author FROM account_bulkuploadtask;"

# Count tasks by status
docker compose exec db mysql -u root -prootpass proj1 \
  -e "SELECT status, COUNT(*) FROM account_bulkuploadtask GROUP BY status;"
```

---

## 🐳 Docker Services

### Services in docker-compose.yml

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| **db** | mysql:8.0 | 3306 | Persistent database (books, users, tasks) |
| **redis** | redis:7-alpine | 6379 | Message broker (task queue) + result storage |
| **web** | proj1:latest | 8000 | Django app (Gunicorn, REST APIs) |
| **celery_worker** | proj1:latest | - | Async task processor (listens to Redis) |

### Start Services

```bash
# Build images
docker compose build --no-cache web

# Start all services
docker compose up --detach db redis web celery_worker

# View logs
docker compose logs -f web celery_worker

# Stop all
docker compose down

# Stop & remove volumes (clean slate)
docker compose down -v
```

### Troubleshooting

**Celery worker crashes:**
```bash
docker compose logs celery_worker
# Check for import errors, missing dependencies
# Rebuild: docker compose build --no-cache web
```

**DB connection timeout:**
```bash
docker compose exec db mysql -u root -prootpass -e "SELECT 1;"
# If fails, db service may not be running: docker compose up --detach db
```

**Redis connection refused:**
```bash
docker compose exec redis redis-cli ping
# Response: PONG (healthy)
```

**Task stuck in "processing":**
```bash
# Check Celery worker logs for exceptions
docker compose logs celery_worker

# Manually reset task (danger: use only for debugging)
docker compose exec db mysql -u root -prootpass proj1 \
  -e "UPDATE account_bulkuploadtask SET status='failed' WHERE status='processing';"
```

---

## 🚀 Performance & Scaling

### Current Configuration
- **Celery concurrency:** 4 (prefork workers)
- **Task delay:** 0.5s per row (configurable)
- **Upload limit:** No hardcoded limit (depends on memory, file size)
- **Batch size:** Unlimited rows per CSV

### Scaling Up

**Increase Celery workers:**
```yaml
# docker-compose.yml
celery_worker:
  ...
  environment:
    CELERY_CONCURRENCY: "8"  # 8 parallel workers
```

**Add multiple worker instances:**
```yaml
celery_worker_1:
  build: .
  command: celery -A proj1 worker --loglevel=info

celery_worker_2:
  build: .
  command: celery -A proj1 worker --loglevel=info

celery_worker_3:
  build: .
  command: celery -A proj1 worker --loglevel=info
```

All workers listen to same Redis queue (automatic load distribution).

---

## 📋 API Response Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | OK (read success) | GET /books/ |
| 201 | Created (signup/create book) | POST /books/ |
| 202 | Accepted (async task enqueued) | POST /bulk-upload/ |
| 400 | Bad Request (missing fields) | POST /login/ without username |
| 401 | Unauthorized (invalid credentials) | Wrong password |
| 403 | Forbidden (ownership check) | Edit book you don't own |
| 404 | Not Found (resource doesn't exist) | GET /books/999/ |
| 500 | Server Error (Django/task failure) | Celery task exception |

---

## 🔐 Security Notes

- **JWT tokens:** Stored in `httponly` cookie (XSS protection)
- **Ownership checks:** All book CRUD operations verify `book.user_id == request.user.id`
- **CSRF exempt:** Only on auth endpoints (JWT handles CSRF security)
- **Password hashing:** Django's PBKDF2 by default
- **Database:** MySQL with prepared statements (SQL injection protection)

---

## 📚 References

- [Django Docs](https://docs.djangoproject.com/en/6.0/)
- [Celery Documentation](https://docs.celeryproject.org/)
- [Redis Documentation](https://redis.io/documentation)
- [DRF JWT](https://django-rest-framework-simplejwt.readthedocs.io/)
- [Colima](https://github.com/abiosoft/colima)

---

## 📝 Notes

- Docker Compose version key is obsolete (remove `version: "3.8"` line)
- Celery worker runs as root (warning — use non-root user in production)
- PyMySQL requires `cryptography` package for MySQL 8's `caching_sha2_password` auth
- All API calls require JWT (use `Authorization: Bearer <token>` header)

---

## ✅ Checklist (Quick Start)

- [ ] Colima running: `colima status`
- [ ] Services up: `docker compose ps`
- [ ] Migrations done: `docker compose run --rm web python manage.py migrate`
- [ ] CSV ready: `test_books.csv` created
- [ ] Signup: POST /signup/
- [ ] Login: POST /login/
- [ ] Upload: POST /bulk-upload/ (with JWT token)
- [ ] Check status: GET /batch-status/?batch_id=...
- [ ] Verify books: GET /books/
- [ ] Monitor logs: `docker compose logs -f celery_worker`

---

**Last Updated:** 2026-01-13  
**Version:** 1.0.0