# Backend Improvement Tasks

- [x] Make DEBUG configurable via environment variable to ease local development and production configuration.
- [x] Add additional security headers (e.g., Content-Security-Policy, Strict-Transport-Security) in custom middleware for better hardening.
- [x] Optimize product list endpoint by reducing verbose logging and adding caching to the list query.
- [x] Standardize MongoDB connection environment variables between settings and connection helper.
- [x] Trigger asynchronous order confirmation emails after order creation using Celery.
