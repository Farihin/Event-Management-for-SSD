# Secure Event Registration (Django)

A small, fully-functional **Event Registration** web app built on Django 5.2 LTS
with OWASP-aligned security controls (authentication, RBAC, secure CRUD, file
uploads, audit logging, hardened configuration).

> This README covers **how to run the project**. (Security/compliance
> documentation is maintained separately.)

## Requirements

- Python 3.11 (the project pins Django 5.2 LTS, which supports 3.11)
- Windows / macOS / Linux

## Setup

```powershell
# 1. Create & activate a virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1          # Windows PowerShell
# source .venv/bin/activate           # macOS/Linux

# 2. Install pinned dependencies
pip install -r requirements.txt

# 3. Create your .env from the template, then set a secret key
copy .env.example .env                 # Windows  (cp on macOS/Linux)
python -c "import secrets; print(secrets.token_urlsafe(64))"
#   -> paste the value into DJANGO_SECRET_KEY in .env

# 4. Apply migrations
python manage.py migrate

# 5. (Optional) load demo data: 1 admin, 1 user, 5 events
python manage.py seed
```

Demo logins created by `seed` (change before any real deployment):

| Role        | Username | Password         |
|-------------|----------|------------------|
| Admin       | `admin`  | `Admin#Secure123`|
| Normal user | `user`   | `User#Secure123` |

To create your own admin instead: `python manage.py createsuperuser`, then set
its role to `ADMIN` in the Django admin (`/admin/`).

## Run (local HTTPS)

The dev server runs over self-signed TLS so secure cookies are exercised:

```powershell
python manage.py runserver_plus --cert-file certs/localhost 127.0.0.1:8000
```

Then open **https://localhost:8000/** and accept the browser's self-signed
certificate warning once. (For a trusted cert with no warning, install
[mkcert](https://github.com/FilipoSofi/mkcert), run `mkcert -install`, then
`mkcert -cert-file certs/localhost.pem -key-file certs/localhost-key.pem localhost 127.0.0.1`
and pass those files to `runserver_plus`.)

> Do **not** add `--noreload`: it is incompatible with the bundled Werkzeug and
> trips a `WERKZEUG_SERVER_FD` error.

Plain HTTP (no TLS, secure cookies won't persist a login) is also available with
`python manage.py runserver`.

### Run with production settings (DEBUG=False)

This activates the custom 400/403/404/500 error pages, HSTS, and enforced CSP.
Static files are served by WhiteNoise, so run `collectstatic` first:

```powershell
python manage.py collectstatic --noinput --settings=eventproject.settings.prod
$env:DJANGO_SETTINGS_MODULE = "eventproject.settings.prod"
python manage.py runserver_plus --cert-file certs/localhost 127.0.0.1:8000
```

Ensure `DJANGO_ALLOWED_HOSTS` in `.env` lists every hostname you serve
(e.g. `127.0.0.1,localhost,django.zahar.my`).

## Tests

```powershell
python manage.py test
```

## Security tooling

```powershell
# Dependency vulnerability scan
pip-audit -r requirements.txt --strict --desc

# Django deployment hardening audit (uses production settings)
python manage.py check --deploy --settings=eventproject.settings.prod
```

## Useful commands

```powershell
# Clear an account lockout during testing (django-axes)
python manage.py axes_reset

# Re-pin dependencies after editing requirements.in
pip-compile requirements.in -o requirements.txt
```

## Project layout

```
eventproject/settings/{base,dev,prod}.py   # split settings (.env-driven)
accounts/   custom user, RBAC, auth, password reset
events/     Event + Registration CRUD (the secure module)
audit/      audit-log model, signals, admin-only log page
core/       base template, custom error pages, upload validators
```
