# Backend Improvement Tasks

- [x] Make DEBUG configurable via environment variable to ease local development and production configuration.
- [x] Add additional security headers (e.g., Content-Security-Policy, Strict-Transport-Security) in custom middleware for better hardening.
- [x] Optimize product list endpoint by reducing verbose logging and adding caching to the list query.
- [x] Standardize MongoDB connection environment variables between settings and connection helper.
- [x] Trigger asynchronous order confirmation emails after order creation using Celery.
- [x] Introduce rate limiting on the login endpoint to mitigate brute-force attacks.

- [x] Add unit tests for `SecurityHeadersMiddleware` to verify required HTTP headers are present.
- [ ] Refactor order creation logic into a service layer to reduce complexity and ensure atomic inventory updates.
- [ ] Implement structured logging with configurable log levels and forward logs to external monitoring.
- [ ] Enforce code linting (e.g., flake8/black) and integrate checks into the CI pipeline.
- [ ] Require email verification for new user signups and send verification emails asynchronously.
- [ ] Provide a `/health/` endpoint for basic application and database connectivity checks.
