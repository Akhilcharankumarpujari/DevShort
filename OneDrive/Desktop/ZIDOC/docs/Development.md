# Developer Guidelines & Coding Standards

This guide covers coding standards, conventions, and practices required to maintain high code quality across the Zidoc platform.

---

## Coding Standards

### Clean Code & SOLID
- **Single Responsibility**: Each module, class, or function must have one reason to change.
- **Dependency Inversion**: Handlers must depend on Usecase interfaces; Usecases must depend on Repository interfaces. Maintain explicit dependency injection in main bootstrappers.
- **Explicit Interfaces**: Mock-ready testable code.

---

## Conventional Commits

We follow the Conventional Commits specification for commit messages:
- `feat`: A new user-facing feature.
- `fix`: A bug fix.
- `docs`: Documentation changes.
- `style`: Code formatting changes (missing semi-colons, whitespace adjustments, etc.).
- `refactor`: Code changes that neither fix a bug nor add a feature.
- `test`: Adding or correcting tests.
- `chore`: Infrastructure updates, dependency increments.

Example:
```bash
feat(auth): add JWT session refresh handler and credentials validation
```

---

## Running Verification Suites

Verify all services locally before proposing pull requests.

### Backend Verification
Run unit tests inside `apps/api`:
```bash
cd apps/api
go test -v ./...
```

### Frontend Verification
Run testing suite inside `apps/web`:
```bash
cd apps/web
npm run test
```

### AI Service Verification
Run pytest inside `apps/ai-service`:
```bash
cd apps/ai-service
pytest
```
