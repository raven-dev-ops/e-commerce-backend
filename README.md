# E-Commerce Backend

This repository contains a Django and MongoEngine based backend for an example e-commerce platform.

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
   ALLOWED_HOSTS=localhost,127.0.0.1
   DATABASE_URL=postgres://user:pass@host:5432/dbname  # or sqlite:///db.sqlite3
   MONGO_URI=mongodb://localhost:27017/dbname
   MONGODB_URI=mongodb://localhost:27017/dbname
   STRIPE_SECRET_KEY=sk_test_your_key
   STRIPE_WEBHOOK_SECRET=whsec_your_key
   GOOGLE_CLIENT_ID=your-google-client-id
   GOOGLE_CLIENT_SECRET=your-google-client-secret
   FACEBOOK_APP_ID=your-facebook-app-id
   FACEBOOK_APP_SECRET=your-facebook-app-secret
   INSTAGRAM_APP_ID=your-instagram-app-id
   INSTAGRAM_APP_SECRET=your-instagram-app-secret
   SENTRY_DSN=your-sentry-dsn
   ```

## Running the Server

Apply migrations and start the development server:
```bash
python manage.py migrate
python manage.py runserver
```
The API will be available at `http://127.0.0.1:8000/`.

## Running Tests

Execute the Django test suite with:
```bash
CI=1 python manage.py test
```
Tests require the same environment variables as the development server. Setting
`CI=1` tells the settings to use the local MongoDB instance defined in
`MONGO_URI` instead of any remote value. When running locally, using SQLite and a
local MongoDB instance is sufficient.
