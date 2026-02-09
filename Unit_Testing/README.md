# Unit Testing Documentation

This directory contains the unit tests for the **Timetable Scheduling System**. The tests are organized by module to ensure comprehensive coverage of both backend and frontend components.

## 📂 Directory Structure

```
Unit_Testing/
├── Module1_RBAC/             # Role-Based Access Control Tests
├── Module2_Data_Ingestion/   # Data Import/Export Tests
├── Module3_Scheuling_Algorithm/ # Scheduling Logic & Algorithm Tests
├── Module4_backend_api/      # Backend API Endpoint Tests
├── Module5_Frontend/         # Frontend Component & Integration Tests
└── README.md                 # This file
```

## 🛠️ Prerequisites

Before running the tests, ensure you have the following installed:

- **Python 3.13+** (for Backend tests)
- **Node.js 18+** & **npm 10+** (for Frontend tests)

## 🚀 Running Tests

### 1. Backend Tests (Python/Django)

The backend tests use `pytest`.

**Setup:**
1. Navigate to the `backend` directory:
   ```bash
   cd ../backend
   ```
2. Activate your virtual environment:
   ```bash
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate     # Windows
   ```
3. Install dependencies (if not already installed):
   ```bash
   pip install -r requirements.txt
   ```

**Run All Tests:**
```bash
pytest
```

**Run Specific Module Tests:**
To run tests for a specific module (e.g., API tests):
```bash
pytest ../Unit_Testing/Module4_backend_api/
```

**Generate Coverage Report:**
```bash
pytest --cov=. --cov-report=html
```

### 2. Frontend Tests (React/Vite)

The frontend tests use `Vitest` and `React Testing Library`.

**Setup:**
1. Navigate to the `frontend` directory:
   ```bash
   cd ../frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```

**Run All Tests:**
```bash
npm test
```

**Run Specific Test File:**
```bash
npx vitest run ../Unit_Testing/Module5_Frontend/App.test.jsx
```

## 📝 Writing New Tests

- **Backend**: Place new test files in the appropriate `ModuleX` folder within `Unit_Testing`. Use `pytest` naming conventions (e.g., `test_*.py` or `*_test.py`).
- **Frontend**: Place new test files in `Module5_Frontend` or alongside components in `src`. Use `.test.jsx` or `.spec.jsx` extensions.

For more detailed guidelines, refer to the [Developer Testing Guide](../docs/Testing_Guide.md).
