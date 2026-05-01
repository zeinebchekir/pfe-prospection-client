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

---

## Lead Scoring - Mise en route pour les membres Git

Cette partie explique comment lancer correctement la fonctionnalite **Lead Scoring** apres avoir recupere la branche Git.

### 1. Recuperer le code

```bash
git pull origin ia-ml-service
```

### 2. Verifier le fichier `.env`

Le fichier `.env` doit exister a la racine du projet. Il doit contenir au minimum les variables suivantes :

```env
SECRET_KEY=your-secret-key
DB_NAME=crmpfe_db
DB_USER=crmpfe_user
DB_PASSWORD=crmpfe_password
DB_HOST=db
DB_PORT=5432
LEAD_SCORING_SERVICE_URL=http://ia-ml:8002
```

### 3. Base vide ou base deja chargee

Le service de scoring utilise la table PostgreSQL suivante :

```sql
public.lead_opportunity
```

Si la base contient deja cette table avec des donnees, passer directement a l'etape Docker.

Si la base est totalement vide, il faut d'abord creer ou importer la table `lead_opportunity`, puis charger les donnees. La migration actuelle ajoute les colonnes de scoring avec `ALTER TABLE`, donc elle suppose que `lead_opportunity` existe deja.

Ordre conseille pour une nouvelle base :

```bash
docker compose up -d db
```

Ensuite, creer/importer la table `lead_opportunity` et charger les donnees via pgAdmin, psql, un dump SQL, ou le script utilise par l'equipe.

### 4. Lancer le projet

```bash
docker compose up -d --build
```

Cette commande construit les services, lance PostgreSQL, lance le backend Django, applique les migrations, lance le frontend, et lance le service IA/ML `ia-ml`.

Verifier ensuite que les services sont actifs :

```bash
docker compose ps
```

Les services importants sont :

- `db`
- `web`
- `frontend`
- `ia-ml`

### 5. Conditions pour entrainer le modele

Avant de lancer l'entrainement, la table `lead_opportunity` doit contenir assez de donnees exploitables :

- au moins `100` lignes ;
- la colonne cible `lead_score` remplie ;
- au moins deux classes dans `lead_score`, par exemple des lignes avec `0` et des lignes avec `1`.

Si ces conditions ne sont pas respectees, l'entrainement du modele echouera.

### 6. Entrainer le modele Lead Scoring

L'entrainement peut etre lance depuis la page **Opportunites** dans l'application, ou via l'API backend :

```http
POST /api/leads/opportunities/train/
```

Apres l'entrainement, le service IA/ML cree automatiquement les artefacts du modele dans :

```text
IA-ML_service/artifacts/lead_scoring/
```

Ce dossier est ignore par Git. Chaque membre doit donc generer son modele localement.

### 7. Verifier que tout marche

Pour verifier le bon fonctionnement :

- ouvrir la page **Opportunites** ;
- verifier que les leads sont affiches ;
- lancer l'entrainement si aucun modele n'existe ;
- verifier que les champs de scoring sont remplis : `lead_score_predicted`, `lead_temperature`, `model_version`, `scored_at` ;
- creer ou modifier un lead et verifier qu'il est score automatiquement.

### Resume rapide

```bash
git pull origin ia-ml-service
docker compose up -d db
# creer/importer lead_opportunity + charger les donnees si la base est vide
docker compose up -d --build
# lancer l'entrainement du modele depuis Opportunites
```

---

## 🗄️ First-Time ETL Setup: `initial_load` DAG

> **This section applies to any developer who clones the repo fresh (or resets Docker volumes).**

### Why this step is needed

After a fresh clone or after running `docker-compose down -v`, the **ETL database is empty**.  
The `entreprise` table (which feeds the segmentation dashboard, leads pages, and BOAMP enrichment) will have **zero rows**.

The `initial_load` Airflow DAG performs a full ETL pipeline:
- Scrapes BOAMP (public tenders) and DataGouv (company registry)
- Extracts, filters, cleans, and enriches the data
- Loads everything into the `entreprise` table

**This DAG is manual-only** (`schedule=None`) — it will never run automatically.

---

### Step 1 — Start the project

```bash
# Copy and fill your environment file first
cp .env.example .env
# Edit .env and set all required secrets

docker-compose up --build -d
```

Wait for all services to be healthy:

```bash
docker-compose ps
```

### Step 2 — Check if initial load is needed

```bash
curl http://localhost:8001/etl/status
```

**If `entreprise` table is empty** (fresh clone):

```json
{
  "status": "ok",
  "database_connected": true,
  "entreprise_count": 0,
  "initial_load_required": true,
  "message": "No company data found. Trigger Airflow DAG initial_load manually."
}
```

**If data already exists** (normal restart or resumed project):

```json
{
  "status": "ok",
  "database_connected": true,
  "entreprise_count": 1244,
  "initial_load_required": false,
  "message": "ETL data is already available."
}
```

You can also use the CLI helper script (requires Python + DB reachable):

```bash
python scripts/check_etl_data.py
```

### Step 3 — Trigger `initial_load` (only if needed)

#### Option A — Airflow UI (recommended)

1. Open **http://localhost:8080**
2. Login with your Airflow credentials (configured in `.env`)
3. Find the DAG named `initial_load`
4. Click the **▶ Trigger** button
5. Wait for all tasks to succeed — this can take **10–30 minutes** depending on API rate limits

#### Option B — ETL API (programmatic)

```bash
curl -X POST http://localhost:8001/etl/trigger-initial-load
```

The endpoint will:
- Check `entreprise_count` first
- Only trigger the DAG if the table is empty
- Return a JSON response with the `dag_run_id` and a link to the Airflow UI

#### Option C — Force trigger (advanced, use with caution)

```bash
curl -X POST "http://localhost:8001/etl/trigger-initial-load?force=true"
```

> ⚠️ **Warning**: `force=true` will trigger even when data exists.  
> This may cause duplicate or overwritten records if the upsert logic is not perfectly idempotent.

### Step 4 — Verify the load completed

```bash
curl http://localhost:8001/etl/status
```

You should see `"initial_load_required": false` and a non-zero `entreprise_count`.

### ⛔ Do NOT re-run `initial_load` unnecessarily

Regular data updates are handled automatically by the **delta DAGs**:

| DAG | Schedule | Purpose |
|-----|----------|---------|
| `sync_datagouv` | Every 6 hours | Incremental company registry updates |
| `sync_boamp` | Daily at 06:00 | New BOAMP public tenders |

Only run `initial_load` again if you:
- Reset Docker volumes (`docker-compose down -v`)
- Intentionally want a full data reload from scratch
- Are onboarding to a completely fresh environment

### Quick reference

```bash
# Check DB state
curl http://localhost:8001/etl/status

# Trigger initial load (safe — won't run if data exists)
curl -X POST http://localhost:8001/etl/trigger-initial-load

# Developer CLI check
python scripts/check_etl_data.py

# Airflow UI
http://localhost:8080

# ETL API docs
http://localhost:8001/docs
```
