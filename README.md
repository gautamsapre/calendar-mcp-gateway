# calendar-mcp-gateway

A capability gateway for safely performing calendar operations backed by Google Calendar.

This project implements a calendar integration service that can list and create meetings (with Google Meet conferencing) while introducing a clear trust boundary between a decision-making system and real-world actions.

The goal is to demonstrate how production systems should handle non-deterministic callers (such as assistants or language models) when interacting with stateful external services.

---

## Why this exists

Modern assistants can reason about user intent and decide what action should be taken:

> “Schedule a meeting tomorrow”
> “Cancel my morning meeting”
> “Move everything after 3 PM”

However, language interpretation is inherently ambiguous.
External systems like calendars, payment systems, or databases are not.

Directly mapping interpreted intent to real actions can cause:

* unintended data modification
* destructive operations
* user trust failures
* irreversible state changes

This project separates:

**Decision** (what should happen)
from
**Execution** (what is allowed to happen)

The calendar service acts as a controlled execution layer that validates and performs operations safely.

---

## Architecture

```
Caller (assistant / AI / UI)
          ↓
Calendar Gateway (this project)
          ↓
Google Calendar API
          ↓
User Calendar
```

The gateway is a deterministic system.

It is responsible for:

* validating operations
* structuring inputs
* controlling permissions
* performing actions on external APIs

The caller is not trusted to execute operations directly.

---

## Features

* OAuth integration with Google Calendar
* List upcoming events
* Create meetings with Google Meet conferencing
* Persistent authentication via refresh tokens
* Clear separation between integration logic and caller logic

---

## Local Setup

### 1. Clone

```bash
git clone <your-repo-url>
cd calendar-mcp-gateway
```

### 2. Python environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .
```

---

## Google Cloud Setup

1. Create a project in Google Cloud Console
2. Enable **Google Calendar API**
3. Configure OAuth consent screen

   * User type: External
   * Publishing status: Testing
   * Add your email as a Test User
4. Create OAuth Client ID

   * Type: Desktop app
5. Download credentials JSON

Place the file in the repo root:

```
credentials.json
```

Do not commit this file.

---

## Verify Calendar Access

This checks authentication and read access.

```bash
python scripts/verify_calendar_access.py
```

You will be prompted to sign in once.
After authorization a `token.json` file will be created locally.

Subsequent runs will not require login.

---

## Create a Meeting with Google Meet

```bash
python scripts/create_meet_meeting.py
```

The script will:

* create a calendar event
* attach a Google Meet link
* print the meeting URL

You should see a new meeting appear in your calendar.

---

## Security Notes

* `credentials.json` and `token.json` must never be committed
* Tokens allow calendar access and should be treated as secrets
* The gateway performs actions on behalf of the authenticated user

---

## Why a Gateway Instead of Direct API Calls?

External APIs assume the caller is correct software.

Language-driven systems are not deterministic.
They interpret user intent.

A gateway allows:

* validation
* confirmation workflows
* audit logging
* safety checks

Without an execution boundary, an assistant could perform unintended destructive actions.

This repository establishes the execution layer that will later be protected by a capability interface.

---

## Next Steps

Planned additions:

* cancellation workflows
* permissioned operations
* audit logging
* MCP capability interface

---

## What this project demonstrates

This repository is not primarily about Google Calendar.

It demonstrates a pattern:

> Real systems should not allow decision-making components to directly mutate external state.

Instead, actions should pass through a controlled capability layer.

This pattern becomes critical when integrating assistants, agents, or other probabilistic systems into real applications.
