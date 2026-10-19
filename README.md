# Ticket Management System

A role-based ticket management API built with **FastAPI**,
**SQLAlchemy**, and **PostgreSQL**. Employees can submit and track
tickets, the IT Head can review and accept or reject them, and the IT
Manager can review tickets escalated after the 24-hour response window.

## Features

-   User signup and login with hashed passwords.
-   JWT bearer-token authentication.
-   Role-based access for `employee`, `it_head`, and `manager`.
-   Employees can create tickets and view their own tickets.
-   IT Head can view all tickets, view pending tickets, accept pending
    tickets, and reject pending tickets with a reason.
-   Pending tickets are escalated after 24 hours without a response.
-   IT Manager can view escalated tickets.
-   Email addresses are normalized to lowercase during signup and
    compared case-insensitively during login.

## Technology

-   Python 3.14 or newer (as specified in `pyproject.toml`)
-   FastAPI
-   SQLAlchemy
-   PostgreSQL with Psycopg 3
-   Pydantic
-   JWT (`python-jose`)
-   Passlib and bcrypt
-   Uvicorn

## Project structure

``` text
NEW_Ticket_Sys/
├── auth.py
├── controllers.py
├── database.py
├── escalation.py
├── main.py
├── models.py
├── pydantic_model.py
├── routers.py
├── set_role.py
├── .env                 # local only; do not commit
├── .gitignore
├── pyproject.toml
├── requirements.txt
├── README.md
└── uv.lock
```

## Setup

### 1. Create and activate a virtual environment

Windows PowerShell:

``` powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, you can run the app with the
environment's Python executable directly or follow your organization's
PowerShell policy.

### 2. Install dependencies

Using `requirements.txt`:

``` powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If you use `uv` and want to use the project's lock file instead:

``` powershell
uv sync
```

### 3. Configure environment variables

Create a local `.env` file in the project root. Do not copy real
credentials into documentation or commit them to Git.

``` dotenv
DATA_BASE=postgresql+psycopg://USERNAME:PASSWORD@HOST:PORT/DATABASE
JWT_SECRET_KEY=replace_with_a_long_random_secret
```

-   `DATA_BASE` is the PostgreSQL connection URL read by `database.py`.
-   `JWT_SECRET_KEY` signs JWT access tokens.
-   Keep `.env` out of version control. Commit a placeholder
    `.env.example` only if needed; never place real secrets in it.
-   If a real database password or JWT secret has ever been committed or
    shared, rotate it.

### 4. Run the API

From the project root:

``` powershell
python -m uvicorn main:app --reload
```

Open the interactive API documentation at:

-   Swagger UI: `http://127.0.0.1:8000/docs`
-   ReDoc: `http://127.0.0.1:8000/redoc`

## Authentication

1.  Create an account using `POST /auth/signup`.
2.  Sign in using `POST /auth/login`.
3.  Copy the returned `access_token`.
4.  In Swagger UI, click **Authorize** and enter the bearer token as
    prompted. Authenticated requests use the
    `Authorization: Bearer <token>` header.
5.  Use `GET /auth/me` to inspect the current account and role.

New signups receive the `employee` role. Use `set_role.py` to assign a
trusted account the `it_head` or `manager` role.

## API endpoints

  ---------------------------------------------------------------------------------------------
  Method            Endpoint                                Access            Purpose
  ----------------- --------------------------------------- ----------------- -----------------
  `POST`            `/auth/signup`                          Public            Create an
                                                                              employee account

  `POST`            `/auth/login`                           Public            Log in and
                                                                              receive a JWT

  `GET`             `/auth/me`                              Authenticated     Return the
                                                                              current user's
                                                                              details

  `POST`            `/tickets`                              Employee          Create a ticket

  `GET`             `/tickets/my`                           Employee          List the
                                                                              employee's own
                                                                              tickets

  `GET`             `/tickets/{ticket_id}`                  Authenticated     Get a ticket;
                                                                              employees can
                                                                              only view their
                                                                              own

  `GET`             `/it-head/tickets`                      IT Head           List all tickets

  `GET`             `/it-head/tickets/pending`              IT Head           List pending
                                                                              tickets

  `PATCH`           `/it-head/tickets/{ticket_id}/accept`   IT Head           Accept a pending
                                                                              ticket

  `PATCH`           `/it-head/tickets/{ticket_id}/reject`   IT Head           Reject a pending
                                                                              ticket with a
                                                                              reason

  `GET`             `/manager/tickets/escalated`            Manager           List escalated
                                                                              tickets
  ---------------------------------------------------------------------------------------------

### Create a ticket example

``` json
{
  "title": "Laptop is not starting",
  "description": "The laptop does not power on when the power button is pressed."
}
```

### Reject a ticket example

Send this JSON body to `PATCH /it-head/tickets/{ticket_id}/reject`:

``` json
{
  "reason": "The request needs additional information."
}
```

## Ticket lifecycle

-   A new ticket starts with status `PENDING`.
-   The IT Head can accept or reject a pending ticket.
-   Rejection requires a non-empty reason.
-   A pending ticket is marked escalated when it has been waiting for 24
    hours or more without a response.
-   The manager endpoint returns tickets whose `is_escalated` flag is
    true.

The app also starts a background loop that checks for overdue tickets
approximately every 60 seconds. The ticket listing functions also run
the escalation check before returning their results.

## Assign a role

Run the script from the project root after the account has signed up:

``` powershell
python set_role.py user@example.com it_head
python set_role.py manager@example.com manager
python set_role.py employee@example.com employee
```

Valid roles are `employee`, `it_head`, and `manager`. Treat role
assignment as an administrative operation; do not expose this script as
a public endpoint.

## Important notes

-   The application calls `Base.metadata.create_all()` during startup.
    This creates missing tables, but it does **not** migrate existing
    tables when models change. Use a migration tool such as Alembic for
    schema changes.
-   The application currently uses synchronous SQLAlchemy sessions.
-   The JWT expiry is configured in `auth.py` (currently 30 minutes).
-   The API should be tested against a development database before use
    with real data.
-   Add automated tests for authentication, role restrictions, ticket
    ownership, rejection reasons, and the 24-hour escalation rule before
    production deployment.

## Suggested manual test checklist

1.  Sign up an employee and log in.
2.  Create a ticket and confirm its status is `PENDING`.
3.  Confirm the employee can list and view their own ticket.
4.  Confirm the employee cannot access IT Head or manager endpoints.
5.  Assign an IT Head role, then test listing, accepting, and rejecting
    pending tickets.
6.  Confirm rejection without a valid reason is rejected.
7.  Assign a manager role and confirm the manager can view escalated
    tickets.
8.  In a test database, create or age a pending ticket beyond 24 hours
    and verify it is escalated.
9.  Confirm employees cannot view another employee's ticket by ID.

## Security

-   Never commit `.env`, passwords, database URLs containing
    credentials, or JWT secrets.
-   Rotate any credentials that were previously exposed.
-   Use a strong, unique JWT secret.
-   Use HTTPS when deployed outside local development.
-   Keep dependencies updated and review access permissions before
    deployment.
