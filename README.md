# Personal Finance App

A multi-user personal finance management application built with Python, Streamlit, PostgreSQL, and Google authentication.

The project started as a personal alternative to managing finances across multiple Excel sheets. The goal is to provide a simple overview of financial position, monthly planning, savings goals, investments, and liquidity in one place.

## Features

- Google authentication
- Multi-user data isolation
- Bank and cash account tracking
- Asset tracking
- Debt tracking
- Virtual savings funds
- Monthly income and allocation planning
- Actual fund contributions
- Investment contributions
- Automatic fund and investment balance updates
- Net worth and liquidity calculations
- User feedback system
- User-controlled data deletion

## Tech Stack

- Python
- Streamlit
- PostgreSQL
- SQLAlchemy
- Neon PostgreSQL
- Google OAuth / OpenID Connect
- Streamlit Community Cloud
- GitHub

## Architecture

User  
↓  
Google OAuth  
↓  
Streamlit application  
↓  
Python business logic  
↓  
SQLAlchemy  
↓  
Neon PostgreSQL

Each authenticated user is mapped to a unique database user ID. Financial records are filtered by ownership to keep data isolated between users.

## How It Works

Users can create accounts, assets, debts and virtual savings funds.

A monthly financial plan can then be created to allocate expected income across expenses, savings funds and investments.

Actual contributions are recorded separately from planned allocations. Fund and investment contributions update the corresponding balances automatically.

This allows the application to distinguish between:

**what the user plans to do with money**  
and  
**what actually happened.**

## Current Status

The application is currently in beta and deployed through Streamlit Community Cloud.

The current stage focuses on testing whether the financial planning model is useful and understandable for real users before investing in more advanced functionality.

## Current Limitations

- Manual financial data entry
- No direct bank integrations
- No automatic market data
- Limited expense transaction tracking
- No native mobile application
- Early-stage UI/UX

## What I Learned

This project gave me practical experience with:

- Python application development
- SQL and relational data modelling
- PostgreSQL
- Multi-user application architecture
- Authentication and OAuth
- Transaction-based financial logic
- Cloud databases
- Cloud deployment
- Git and GitHub
- Product testing and user feedback

## Author

Dominykas

Built as a personal project combining finance, data, and product development.
