# Project Rules

## Product

This is a manual-entry personal finance MVP built with Python, Streamlit, SQLAlchemy and PostgreSQL.

Do not implement bank integrations.

## Safety

Never read, print, modify or commit:
- .env
- .streamlit/secrets.toml
- database credentials
- OAuth secrets

Users should never be asked to enter:
- bank login credentials
- card numbers
- PIN codes
- banking passwords

## Existing Users

Never force existing users with financial data to repeat onboarding.

Never delete or overwrite existing financial data as part of onboarding.

New onboarding must preserve compatibility with existing users and their data.

## Architecture

Prefer:

UI
→ business logic
→ database access
→ SQLAlchemy/PostgreSQL

Do not put large amounts of financial business logic directly inside Streamlit UI event handlers.

Reuse existing business logic wherever possible.

The Streamlit frontend may later be replaced with a web or mobile frontend, so keep financial logic reasonably separated from presentation logic.

## Development

Make the smallest safe change.

Do not perform broad refactors unless explicitly requested.

Do not change database schemas without explaining why first.

Do not change authentication, user ownership, contribution or balance logic casually.

Work on one task at a time.

Before risky or destructive changes, explain the plan and wait for approval.

Preserve currently working functionality.

## Git

Work on the current development branch.

Do not force push.

Do not push directly to main.

Do not rewrite working Git history.

## Current Priority

The current priority is onboarding and UX, NOT adding major new financial features.

Target onboarding:

Welcome
→ Accounts
→ Assets
→ Debts
→ Funds
→ Monthly Plan
→ Financial Picture
→ Existing Dashboard

Existing users who already have financial data should skip onboarding and go directly to their dashboard.

## UX Principles

Keep onboarding simple and progressive.

Do not show too many fields at once.

Explain financial terminology in plain language.

Use:
- short explanations
- examples
- placeholders
- tooltips
- progress indicators
- optional advanced explanations

Encourage users during onboarding without adding unnecessary text.

The user should understand what they are doing and why before moving to the next step.

## Working With Me

I am learning software development.

For important changes:
1. Explain what you found.
2. Explain what you plan to change.
3. Make the smallest sensible implementation.
4. Tell me which files were changed.
5. Explain important code or architecture decisions.
6. Run relevant checks/tests when practical.

Do not hide unnecessary complexity from me. Help me understand the project as we build it.