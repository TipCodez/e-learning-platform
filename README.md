# Acadeval

Acadeval is a Django Templates online learning and certification platform. Phase 1 establishes the production-ready foundation: Django settings, role-based authentication, custom profiles, public pages, dashboards, Bootstrap 5 UI, static/media handling, and environment-based configuration.

## Phase 1 Folder Structure

```text
e-platform/
  acadeval/           # Django project settings, URLs, ASGI/WSGI
  accounts/           # Custom user, roles, profiles, auth views/forms/admin
  core/               # Public pages and landing page routes
  dashboards/         # Role-aware dashboards
  templates/          # Base, auth, public, and dashboard templates
  static/             # CSS and JavaScript
  media/              # Development uploads
  logs/               # Runtime logs placeholder
  manage.py
  requirements.txt
  .env.example
```

## Commands to Run

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python manage.py makemigrations accounts
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_demo
python manage.py runserver
```

Open `http://127.0.0.1:8000/`.

## What Phase 1 Includes

- `acadeval/settings.py` configures installed apps, SQLite by default, PostgreSQL through `DATABASE_URL`, static/media files, email settings, security defaults, and the custom user model.
- `accounts/models.py` defines `CustomUser`, `StudentProfile`, `InstructorProfile`, and `OrganizationProfile`.
- `accounts/forms.py` provides registration and profile setup forms.
- `accounts/views.py` handles registration, login, logout, profile setup, and profile display.
- `dashboards/views.py` routes each authenticated user to the correct dashboard and blocks unauthorized role access.
- `templates/base.html` and partials provide reusable UI structure.
- `static/css/acadeval.css` defines the Acadeval visual system, responsive dashboards, hover effects, progress animation, and auth styling.

## How to Test Phase 1

1. Run migrations and start the server.
2. Visit `/` and confirm the landing page loads.
3. Visit `/accounts/register/` and create one account for each role.
4. Confirm each role redirects to its own dashboard after login.
5. Visit `/admin/` with a superuser and confirm users and profiles are manageable.
6. Run `python manage.py seed_demo` and confirm demo courses, badges, plans, and paths appear on the public pages.
7. Test password reset locally. The default email backend prints reset links to the console.

## Common Errors and Fixes

- `ModuleNotFoundError: django`: activate the virtual environment and run `pip install -r requirements.txt`.
- `no such table: accounts_customuser`: run `python manage.py makemigrations accounts` then `python manage.py migrate`.
- Static files look unstyled in production: run `python manage.py collectstatic` and configure the web server to serve `STATIC_ROOT`.
- PostgreSQL connection fails: verify `DATABASE_URL`, database name, username, password, and that PostgreSQL is running.
- Profile image upload fails: install Pillow and confirm `MEDIA_ROOT` is writable.

## Deployment

This repo includes first-pass production deployment files for Render-compatible hosting:

- `Procfile` starts Gunicorn with `acadeval.wsgi`.
- `build.sh` installs dependencies, collects static files, and applies migrations.
- `render.yaml` defines a Python web service, PostgreSQL database, and `/health/` health check.

For production, set these environment variables before deploying:

```bash
DEBUG=False
SECRET_KEY=<long-random-secret>
ALLOWED_HOSTS=<your-domain>,<your-render-host>
CSRF_TRUSTED_ORIGINS=https://<your-domain>,https://<your-render-host>
SECURE_SSL_REDIRECT=True
DATABASE_URL=<postgres-connection-string>
MEDIA_ROOT=/opt/render/project/src/media
```

Uploaded media on ephemeral hosts should use a persistent disk or cloud storage. Public media is intentionally limited to approved upload prefixes; private learner submissions remain blocked from direct public URLs.

## Production Checklist

- Set `DEBUG=False`.
- Replace `SECRET_KEY`.
- Configure `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`.
- Use PostgreSQL through `DATABASE_URL`.
- Configure SMTP email credentials.
- Store payment provider keys only in environment variables.
- Serve static files from `STATIC_ROOT` and media through a cloud-ready storage layer.
- Enable HTTPS, secure cookies, HSTS, backups, monitoring, and file upload validation policies.

## Next Phase

Phase 2 should add the `courses` app with categories, subcategories, courses, modules, lessons, resources, publishing workflow, approval status, search, filters, and course detail pages.

