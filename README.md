# Inventory Management System

A FastAPI-based inventory management system with comprehensive CRUD operations and business logic.

## Features

- User Management with Role-based Access Control
- Inventory Management and Stock Tracking
- Order Management with Status Workflows
- Purchase Management and Supplier Operations
- Warehouse Management
- Audit Logging and Security

## Tech Stack

- Python 3.11+
- FastAPI for API framework
- SQLModel for ORM
- PostgreSQL for database
- Async operations with SQLAlchemy
- JWT-based authentication

## Project Structure

```
backend/
├── alembic/            # Database migrations
├── api/                # API endpoints
├── core/              # Core functionality
│   ├── config.py     # Configuration settings
│   ├── database.py   # Database connection
│   ├── security.py   # Authentication & security
│   └── exceptions.py # Custom exceptions
├── crud/              # Database CRUD operations
│   ├── base.py       # Base CRUD class
│   ├── user/         # User management
│   ├── inventory/    # Inventory management
│   ├── order/       # Order management
│   └── warehouse/   # Warehouse management
├── model/            # Database models
└── schema/          # Pydantic schemas
```

## Setup

1. Create a virtual environment:
   ```bash
   python -m venv env
   source env/bin/activate  # Unix
   .\env\Scripts\activate   # Windows
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables in `.env`:
   ```
   DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/dbname
   SECRET_KEY=your-secret-key
   ```

4. Run migrations:
   ```bash
   alembic upgrade head
   ```

5. Start the server:
   ```bash
   uvicorn main:app --reload
   ```

## API Documentation

Once running, access the API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Development

- Follow PEP 8 style guide
- Write docstrings for all functions
- Add type hints
- Include tests for new features
- Use async/await for database operations

## License

MIT License