import atexit
import logging
import os
import pandas as pd
import streamlit as st

from datetime import date, datetime as dt
from sqlalchemy import create_engine
from sqlalchemy.orm import configure_mappers, sessionmaker

from plog.models.common import Base
from plog.models.milestone import Milestone
from plog.models.project import Project


# Set logging level
logging.basicConfig(level=logging.INFO)

# Define global database engine and session variables.
engine = None
session = None

def init():
    """
    Initializes the streamlit application.
    """
    global engine, session
    # Create database engine and session.
    if 'session' not in st.session_state:
        logging.info("Creating database engine and session.")
        db_path = os.path.abspath("plog.sqlite")
        configure_mappers()
        engine = create_engine(f'sqlite:///{db_path}')
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        # Save engine and database session in streamlit session.
        st.session_state['engine'] = engine
        st.session_state['session'] = session

def shutdown():
    """
    Shutdown the streamlit application.
    """
    global engine, session
    logging.info("Shutting down application.")
    if session is not None:
        logging.info("Closing database session and disposing engine.")
        session.close()
        engine.dispose()

# Run on_shutdown before the python interpreter exits.
atexit.register(shutdown)

def parse_date(val):
    """
    Convert string to date if needed.
    """
    if val is None or val == '':
        return None
    if isinstance(val, date):
        return val
    try:
        return dt.fromisoformat(val).date()
    except Exception:
        try:
            return dt.strptime(val, "%Y-%m-%d").date()
        except Exception:
            return None

def create_form(instance, columns, button_label="Submit"):
    """
    Create a Streamlit form dialog for editing the given SQLAlchemy instance's columns.
    The form fields are generated for the columns in the provided list.
    The form values are directly assigned to the instance.
    Returns True if the form was submitted, otherwise False.
    """

    with st.form("edit_form", clear_on_submit=False):
        for col in columns:
            val = getattr(instance, col, None)
            # Choose widget type based on value type
            if isinstance(val, str) or val is None:
                new_val = st.text_input(col.replace('_', ' ').capitalize(), value=val or "")
            elif isinstance(val, int):
                new_val = st.number_input(col.replace('_', ' ').capitalize(), value=val, step=1)
            elif isinstance(val, float):
                new_val = st.number_input(col.replace('_', ' ').capitalize(), value=val, format="%f")
            elif isinstance(val, date):
                new_val = st.date_input(col.replace('_', ' ').capitalize(), value=pd.to_datetime(val) if val else None, format="YYYY-MM-DD")
            else:
                # Fallback to string input
                new_val = st.text_input(col.replace('_', ' ').capitalize(), value=str(val) if val is not None else "")
            # Assign value if not empty
            if new_val not in ["", [], {}, ()]:
                setattr(instance, col, new_val)
        submitted = st.form_submit_button(button_label)
        cancel = st.form_submit_button("Cancel")
        if cancel:
            st.info("Edit cancelled.")
            return st.rerun()
        return submitted