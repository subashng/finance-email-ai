# Email Assistant Dashboard

AI-powered finance email automation for processing incoming Gmail finance inquiries, verifying customer-specific financial data against authoritative SQL records, applying policy retrieval and safety guardrails, sending approved responses, recording an audit trail, and presenting business outcomes in a manager-focused dashboard.

## Architecture

```text
Gmail Inbox
    |
    v
Finance Email Router
    |
    +---- Non-finance email ----> Ignore
    |
    v
Agent 1 - Finance Email Analysis
    |
    v
Authoritative SQL Finance Data
    |
    v
Agent 2 - Finance Verification
    |
    v
Guardrails
    |
    v
Agent 3 - Finalization
    |
    v
Gmail Reply
    |
    v
Audit Database
    |
    v
Email Assistant Dashboard
```

## Key Capabilities

- Reads real Gmail inbox messages.
- Routes finance-related emails and ignores unrelated system/security/newsletter messages.
- Identifies customers and retrieves authoritative finance records from SQL.
- Uses approved finance policy RAG for general policy guidance.
- Performs deterministic verification of financial claims.
- Keeps deterministic finance verification authoritative over semantic LLM review.
- Applies customer-facing guardrails before sending.
- Preserves the original customer email in the audit record.
- Sends approved replies through Gmail.
- Records workflow and send outcomes in SQLite/SQLAlchemy.
- Provides a dark manager dashboard focused on business outcomes.

## Manager Dashboard

The manager view focuses on business KPIs rather than internal AI decisions.

Typical KPIs include:

- Finance emails received
- Emails processed
- Emails answered
- Exceptions
- Response rate
- New emails
- Average response time
- Benchmark response time

Internal Agent 1 / Agent 2 / Agent 3 / Guardrails decisions are not the primary manager-facing view.

## Demonstrated End-to-End Flow

The project has been tested successfully with real Gmail messages.

Examples demonstrated during development:

- `Outstanding Invoice Inquiry` -> detected -> processed -> approved -> sent.
- `Payment Status Inquiry` -> detected -> processed -> approved -> sent.
- Unrelated Google/SerpApi messages -> ignored.
- Dashboard -> updated from real Gmail/audit results.

## Project Structure

```text
finance_email_ai/
|
+-- app/
|   +-- agents/
|   +-- database/
|   +-- gmail/
|   +-- guardrails/
|   +-- rag/
|   +-- tools/
|   +-- dashboard.py
|   +-- workflow.py
|   +-- send_workflow.py
|
+-- tests/
+-- data/
+-- .env
+-- credentials.json
+-- token.json
+-- README.md
+-- requirements.txt
+-- .gitignore
```

## Setup

### Create and activate the virtual environment

Windows:

```cmd
python -m venv .venv
.venv\Scripts\activate
```

### Install dependencies

```cmd
python -m pip install -r requirements.txt
```

### Environment variables

Create `.env` from `.env.example` and configure the required API settings.

Do not commit `.env`.

### Gmail OAuth

Keep the Gmail OAuth files local:

```text
credentials.json
token.json
```

Do not commit these files.

### Initialize the database

```cmd
python -c "from app.database.database import initialize_database; initialize_database(); print('DATABASE READY')"
```

## Run the Dashboard

```cmd
python -m streamlit run app\dashboard.py
```

Open:

```text
http://localhost:8501
```

The dashboard uses live Gmail data and the workflow audit database.

## Process New Gmail Messages

The current inbox processor is poll-based:

```cmd
python -c "from app.gmail.inbox_processor import process_new_inbox_emails; r=process_new_inbox_emails(); print(r)"
```

Processing flow:

1. Read incoming Gmail messages.
2. Route strong finance-intent messages.
3. Ignore unrelated messages.
4. Skip messages already represented in the audit table.
5. Run the Finance Email AI workflow.
6. Send approved responses.
7. Record the result.

For production, the polling function should be hosted as a persistent worker/service or replaced with an event-driven mailbox listener.

## Testing

Syntax checks:

```cmd
python -m py_compile app\agents\finance_email_agent.py
python -m py_compile app\agents\verification_agent.py
python -m py_compile app\dashboard.py
```

Evaluation suite:

```cmd
python -c "from app.evaluation.runner import run_evaluation_case; from app.evaluation.cases import EVALUATION_CASES; from app.evaluation.evaluator import run_evaluation_suite, print_evaluation_summary; r=run_evaluation_suite(EVALUATION_CASES, run_evaluation_case); print_evaluation_summary(r)"
```

The evaluation suite reached a 100% pass result during development.

## Audit Trail

The audit repository records business and workflow information such as:

- Customer email ID
- Incoming Gmail message ID
- Gmail thread ID
- Subject
- Original customer email
- Action taken
- Workflow status
- Send status
- Processing timings
- Gmail identifiers

The original customer message is preserved for traceability.

## Security

Never commit:

```text
.env
credentials.json
token.json
.venv/
*.db
```

Use:

```cmd
git status
git diff
```

before the first push to confirm no secrets or local runtime data are included.

## GitHub

Initialize:

```cmd
git init
git add .
git commit -m "Initial Email Assistant Dashboard project"
```

Connect your GitHub repository:

```cmd
git remote add origin https://github.com/<YOUR_USERNAME>/<YOUR_REPOSITORY>.git
git branch -M main
git push -u origin main
```

## Production Hardening

Before production deployment, consider:

- Continuous inbox monitoring instead of manual polling.
- Idempotent processing across restarts.
- Retry/error handling and dead-letter processing.
- Stronger customer identity controls.
- Centralized secret management.
- Production database instead of local SQLite.
- Structured logging and observability.
- Role-based dashboard access.
- Privacy and security controls for financial data.
- Automated regression tests and CI/CD.

## Project Description

> AI-powered finance email assistant that automates incoming Gmail finance inquiries using customer-specific SQL verification, policy RAG, deterministic financial validation, safety guardrails, automated Gmail responses, audit trails, and a manager-focused operations dashboard.
