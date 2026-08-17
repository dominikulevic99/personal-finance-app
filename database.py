import os

import streamlit as st

from dotenv import load_dotenv
from sqlalchemy import create_engine


# =========================================================
# LOAD LOCAL ENVIRONMENT
# =========================================================

load_dotenv()


# =========================================================
# GET DATABASE URL
# =========================================================

database_url = os.getenv("DATABASE_URL")

if not database_url:

    database_url = st.secrets.get(
        "DATABASE_URL",
        None
    )

if not database_url:

    raise RuntimeError(
        "DATABASE_URL is missing."
    )


# =========================================================
# DATABASE ENGINE
# =========================================================

engine = create_engine(
    database_url,
    pool_pre_ping=True,
    pool_recycle=300
)
