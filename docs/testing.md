# Testing & Validation Guide

This document describes how to execute automated test suites and validate system components.

## Running Backend Pytests

The backend contains unit and integration tests using `pytest` and `httpx.AsyncClient` mapping against mock database engines.

### Execute Tests Locally:
1. Ensure dependencies are installed inside your virtual environment:
```bash
pip install -r requirements.txt
```
2. Execute pytest from the backend root folder:
```bash
pytest tests/ -v
```

---

## Running Frontend Unit Tests

The frontend is structured to run unit tests using `@testing-library/react` and Vitest:
```bash
cd frontend
npm run test
```

---

## Manual E2E Validation Flow
1. Start the containers using `docker compose up`.
2. Login to the application dashboard at `http://localhost:5173`.
3. Create a queue (e.g. `test-queue`) with concurrency limit 5.
4. Submit a test job containing a simulated delay parameter `{"duration": 5}`.
5. Verify the state transitions:
   - status: `queued`
   - status: `running`
   - status: `completed` (view duration and logs in the inspector panel).
