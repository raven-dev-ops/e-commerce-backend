# E-Commerce Backend

This repository contains a Django-based backend for an example e-commerce platform.

> **Usage & License Notice**
>
> This project is **not open source**. You must obtain explicit written permission from the repository owner before using, copying, modifying, or distributing any part of this codebase.
>
> **Private forks or other private copies of this repository are not allowed** for any purpose. Any fork or clone that the owner expressly permits must remain public and clearly reference this repository.

## Quickstart for Contributors

> Only collaborators who have received explicit written permission from the owner may contribute. Do **not** create private forks or private copies of this repository.

Get a local development instance running with the following commands:

```bash
git clone <repo-url>
cd e-commerce-backend
python -m venv venv
source venv/bin/activate
cp .env.example .env
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_sample_data  # optional
python manage.py runserver
```

In a separate terminal, start a Celery worker for background tasks:

```bash
celery -A backend worker -l info
```

The API will be available at `http://127.0.0.1:8000/`.

## Developer Onboarding

> These steps apply only to authorized collaborators. If you have not received explicit permission from the owner, you are not allowed to use this codebase or fork the repository (including private forks).

New contributors can get started quickly by following these steps:

1. **Fork and clone the repository**
   ```bash
   git clone <your-fork-url>
   cd e-commerce-backend
   ```
2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```
3. **Install dependencies and set up environment variables**
   ```bash
   cp .env.example .env
   pip install -r requirements.txt
   ```
4. **Run database migrations and optional seed data**
   ```bash
   python manage.py migrate
   python manage.py seed_sample_data  # optional
   ```
5. **Verify the setup by running tests and lint checks**
   ```bash
   pre-commit run --files <files you changed>
   CI=1 python manage.py test
   ```
6. **Start the development server and Celery worker**
   ```bash
   python manage.py runserver
   celery -A backend worker -l info
   ```

With the server running you can begin making changes and submitting pull requests.

## Environment Setup

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd e-commerce-backend
   ```
2. **Create a virtual environment and install dependencies**
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. **Create a `.env` file** in the project root. You can start from the included `.env.example`:
   ```bash
   cp .env.example .env
   ```
   Then define the following variables (replace placeholder values with your own):
   ```env
   SECRET_KEY=your-django-secret-key
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1
   DATABASE_URL=postgres://user:pass@host:5432/dbname  # or sqlite:///db.sqlite3
   ERP_API_URL=https://erp.example.com
   ERP_API_KEY=your-erp-api-key
   STRIPE_SECRET_KEY=sk_test_your_key
   STRIPE_WEBHOOK_SECRET=whsec_your_key
   GOOGLE_CLIENT_ID=your-google-client-id
   GOOGLE_CLIENT_SECRET=your-google-client-secret
   FACEBOOK_APP_ID=your-facebook-app-id
   FACEBOOK_APP_SECRET=your-facebook-app-secret
   INSTAGRAM_APP_ID=your-instagram-app-id
   INSTAGRAM_APP_SECRET=your-instagram-app-secret
   SENTRY_DSN=https://examplePublicKey@o0.ingest.sentry.io/0
   DD_AGENT_HOST=localhost
   DD_TRACE_AGENT_PORT=8126
   DD_SERVICE=ecommerce-backend
   DD_ENV=development
   SECURE_SSL_REDIRECT=True
   GLOBAL_ANON_THROTTLE_RATE=100/day
   GLOBAL_USER_THROTTLE_RATE=1000/day
   CORS_ALLOWED_ORIGINS=https://your-frontend-domain.com,http://localhost:3000
   PERSONAL_DATA_RETENTION_DAYS=365  # days to retain inactive user data before purging
```

Setting `SENTRY_DSN` enables centralized error tracking with Sentry for both Django and Celery tasks.
Providing `DD_AGENT_HOST` and related variables enables DataDog APM tracing.

### Stripe

Stripe integration requires two environment variables:

- `STRIPE_SECRET_KEY` – used for server-side Stripe API calls.
- `STRIPE_WEBHOOK_SECRET` – used to verify incoming webhooks.

Without these values, checkout and webhook endpoints will return server errors.

## Docker Compose

A `docker-compose.yml` file is provided to run the application with PostgreSQL, Redis and a Celery worker.
Create a `.env` file as above and then start the stack:

```bash
docker compose up --build
```

The API will be available at `http://localhost:8000/`. Endpoints are versioned under paths like `/api/v1/`.

## Running the Server

Apply migrations and start the development server:
```bash
python manage.py migrate
python manage.py runserver
```
The API will be available at `http://127.0.0.1:8000/`. Endpoints are versioned under paths like `/api/v1/`.

## API Documentation

Swagger UI is available once the server is running:

```
http://127.0.0.1:8000/api/docs/
```

The raw OpenAPI schema can be retrieved from:

```
http://127.0.0.1:8000/api/schema/
```

A ReDoc view is also available at `/api/redoc/`.

## Authentication

Most API endpoints require an authenticated user. Obtain an access token by
sending a `POST` request to the login endpoint:

```bash
curl -X POST http://localhost:8000/api/v1/authentication/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "your-password"}'
```

The response includes an access token:

```json
{
  "user": { "id": 1, "email": "user@example.com" },
  "tokens": { "access": "abc123" }
}
```

Include this token in the `Authorization` header when calling protected
endpoints:

```http
Authorization: Token abc123
```

Endpoints that use JWT authentication (such as the reviews and orders APIs)
expect the token as a Bearer token:

```http
Authorization: Bearer abc123
```

Register new users via `POST /authentication/register/` and verify email
addresses using the link sent to the provided email account.

## Running Celery Workers

Asynchronous tasks are handled with Celery. Start a worker with:

```bash
celery -A backend worker -l info
```

Celery uses Redis by default. Configure `CELERY_BROKER_URL` and
`CELERY_RESULT_BACKEND` in your `.env` file if you need to adjust the connection.

### Caching

The application uses Redis for caching frequently accessed data. Set `CACHE_URL`
in your `.env` file to point to your Redis instance:

```env
CACHE_URL=redis://localhost:6379/1
```

For deployments using a Redis cluster, provide a comma-separated list of node
URLs via `CACHE_URLS`:

```env
CACHE_URLS=redis://cache1:6379/1,redis://cache2:6379/1,redis://cache3:6379/1
```

### Feature Flags

This project uses [django-waffle](https://waffle.readthedocs.io/) to manage feature flags for gradual rollouts. Create and toggle flags in the Django admin and check them in code with helpers like `waffle.flag_is_active(request, "my_flag")`.


## Running Tests

Execute the Django test suite with:
```bash
python manage.py test
```
Tests require the same environment variables as the development server. Ensure
`DATABASE_URL` points to a database that is reachable from your environment
or is unset to fall back to SQLite for local development.

## Sample Data

Populate the database with a demo user and sample products for development:

```bash
python manage.py seed_sample_data
```

By default, the command generates a random password for the `demo` user and
prints it to the console. To use a custom password, set the
`DEMO_USER_PASSWORD` environment variable before running the command.

## Python API Client

A minimal Python SDK is available in the `sdk` package for interacting with the API.

```python
from sdk import ECommerceClient

client = ECommerceClient("https://api.example.com", token="your-api-token")
```

## License & Usage

- This project is licensed under a **proprietary license**; see `LICENSE` in the repository root.
- You must obtain **explicit written permission** from the owner before using, copying, modifying, or distributing this codebase.
- **Private forks or any other private copies are not permitted.** Any fork or clone that the owner expressly permits must remain public and clearly attribute this repository and its owner.
products = client.get_products()
```
