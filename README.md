# 🔐 CrmPfe — Production-Ready Full-Stack Auth System

A secure, production-grade authentication system built with:

- **Backend**: Django 5 + Django REST Framework + SimpleJWT
- **Frontend**: Vue 3 (Composition API) + Vite
- **Database**: PostgreSQL 16
- **Auth strategy**: JWT in HTTP-only cookies (never localStorage)
- **Containerisation**: Docker + Docker Compose

---

## 📁 Project Structure

```
CrmPfe/
├── backend/
│   ├── config/
│   │   ├── settings/
│   │   │   ├── base.py         # Shared settings
│   │   │   ├── dev.py          # Development overrides
│   │   │   └── prod.py         # Production overrides
│   │   ├── urls.py
│   │   ├── wsgi.py
│   │   └── asgi.py
│   ├── apps/
│   │   └── users/
│   │       ├── models.py        # Custom email-based User model
│   │       ├── serializers.py   # Register, Login, Profile serializers
│   │       ├── views.py         # Auth API views
│   │       ├── urls.py
│   │       ├── authentication.py # CookieJWTAuthentication
│   │       ├── utils.py         # Cookie set/unset helpers
│   │       ├── exceptions.py    # Custom exception handler
│   │       ├── admin.py
│   │       └── tests.py         # Auth endpoint tests
│   ├── manage.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── entrypoint.sh
├── frontend/
│   ├── src/
│   │   ├── api/axios.js         # Axios + CSRF + 401 interceptor
│   │   ├── composables/useAuth.js
│   │   ├── router/index.js      # Navigation guards
│   │   ├── pages/
│   │   │   ├── LoginPage.vue
│   │   │   ├── RegisterPage.vue
│   │   │   └── DashboardPage.vue
│   │   ├── App.vue
│   │   ├── main.js
│   │   └── style.css
│   ├── index.html
│   ├── package.json
│   └── vite.config.js          # Dev proxy /api → :8000
├── docker-compose.yml
└── .env.example
```

---

## 🚀 Quick Start (Docker)

### 1. Clone & configure environment

```bash
# Copy the example env file
cp .env.example .env

# Edit .env — set a strong SECRET_KEY:
# SECRET_KEY=your-very-long-random-secret-key-here
```

### 2. Run with Docker Compose

```bash
docker-compose up --build
```

The backend will:
1. Wait for PostgreSQL to be healthy
2. Run `migrate` automatically
3. Collect static files
4. Start Gunicorn on port 8000

### 3. Start the frontend (separate terminal)

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**

---

## 🧑‍💻 Local Development (without Docker)

### Backend

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

pip install -r requirements.txt

# Copy env and configure PostgreSQL credentials
cp ../.env.example ../.env

# Run migrations
python manage.py migrate --settings=config.settings.dev

# Create superuser (optional)
python manage.py createsuperuser --settings=config.settings.dev

# Start dev server
python manage.py runserver --settings=config.settings.dev
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## 🧪 Running Tests

```bash
# Docker
docker-compose exec web python manage.py test apps.users --settings=config.settings.dev -v 2

# Local
cd backend
python manage.py test apps.users --settings=config.settings.dev -v 2
```

Test coverage:
- ✅ Register: success, duplicate email, password mismatch, weak password
- ✅ Login: valid credentials (cookies set + httpOnly), wrong password, inactive user
- ✅ Logout: clears cookies, requires auth
- ✅ Refresh: valid / missing / invalid token
- ✅ Me: returns profile, 401 without cookie, no password in response

---

## 🔌 API Endpoints

| Method | Endpoint | Auth Required | Description |
|--------|----------|:---:|-------------|
| POST | `/api/auth/register/` | ❌ | Create account, set JWT cookies |
| POST | `/api/auth/login/` | ❌ | Login, set JWT cookies |
| POST | `/api/auth/logout/` | ✅ | Blacklist token, clear cookies |
| POST | `/api/auth/refresh/` | ❌ | Rotate tokens via cookie |
| GET  | `/api/auth/me/` | ✅ | Return authenticated user profile |

---

## 🔒 Security Architecture

### Token Storage
- **No localStorage** — immune to XSS token theft
- **HTTP-only cookies** — JavaScript cannot read them (`document.cookie` returns empty)
- **Secure flag** — cookies only sent over HTTPS (enabled in production)
- **SameSite=Lax** — CSRF protection at the browser level

### Token Lifecycle
| Token | Lifetime | Cookie |
|-------|----------|--------|
| Access | 10 minutes | `access_token` |
| Refresh | 7 days | `refresh_token` |

- **Refresh rotation**: every `/refresh/` call issues a new refresh token and blacklists the old one
- **Blacklist app**: prevents replay attacks with old refresh tokens
- **Auto-refresh**: Axios interceptor transparently refreshes on 401 and retries the original request

### CSRF Protection
- Django's CSRF middleware is **enabled**
- The `csrftoken` cookie is **not** HttpOnly (by design) so Axios can read it
- Axios `request interceptor` reads `csrftoken` and sends it as `X-CSRFToken` header on all mutating requests

### Password Security
- Django's default PBKDF2-SHA256 hashing (300,000 iterations in Django 5)
- 4 password validators enabled (similarity, minimum length, common passwords, numeric-only)

### CORS
- `CORS_ALLOW_CREDENTIALS = True` — required for cross-origin cookie delivery
- `CORS_ALLOWED_ORIGINS` restricted to the configured frontend origin

---

## ⚙️ Environment Variables

| Variable | Example | Description |
|----------|---------|-------------|
| `SECRET_KEY` | `ChangeMe!` | Django secret key |
| `DEBUG` | `True` | Debug mode |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Allowed hosts |
| `CSRF_TRUSTED_ORIGINS` | `http://localhost:5173` | CSRF trusted origins |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:5173` | CORS allowed origins |
| `DB_NAME` | `crmpfe_db` | PostgreSQL database name |
| `DB_USER` | `crmpfe_user` | PostgreSQL user |
| `DB_PASSWORD` | `crmpfe_password` | PostgreSQL password |
| `DB_HOST` | `db` | PostgreSQL host (service name in Docker) |
| `DB_PORT` | `5432` | PostgreSQL port |
| `COOKIE_SECURE` | `False` | Set `True` in production (HTTPS only) |

---

## 🐳 Docker Services

| Service | Image | Port |
|---------|-------|------|
| `db` | postgres:16-alpine | 5432 (internal) |
| `web` | Python 3.12 (custom) | 8000 |

---

## 🏭 Production Checklist

- [ ] Set `COOKIE_SECURE=True` (requires HTTPS)
- [ ] Use `config.settings.prod` (`DJANGO_SETTINGS_MODULE`)
- [ ] Set a strong, random `SECRET_KEY`
- [ ] Configure real `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS`
- [ ] Put Nginx/Caddy in front of Gunicorn as a reverse proxy
- [ ] Set `DEBUG=False`
- [ ] Configure proper logging aggregation
- [ ] Set up database backups
