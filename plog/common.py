import atexit
import logging
import os
import pandas as pd
import streamlit as st

from datetime import date, datetime as dt
from sqlalchemy import create_engine, Date, String, Text
from sqlalchemy.orm import class_mapper, configure_mappers, sessionmaker

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

def create_form(instance, columns, options=None, session=None, button_label="Submit"):
    """
    Create a Streamlit form dialog for editing the given SQLAlchemy instance's 
    columns.

    :param instance: SQLAlchemy model instance to be edited.
    :type instance: object
    :param columns: Dictionary mapping column names to labels for the form fields.
    :type columns: dict[str, str]
    :param options: Dictionary mapping column names to options for selection boxes.
    :type options: dict[str, dict[str, object]]
    :param button_label: Label for the submit button (default: "Submit").
    :type button_label: str
    :returns: True if the form was submitted, otherwise False.
    :rtype: bool
    """
    # Check if session is provided, otherwise use the one from session state.
    if session is None:
        session = st.session_state['session']

    # Create edit form for specified columns.
    with st.form("edit_form", clear_on_submit=False):
        mapper = class_mapper(type(instance))
        for col, label in columns.items():
            val = getattr(instance, col, None)

            # Detect SQLAlchemy column type
            sa_col_type = None
            if hasattr(mapper, 'columns') and col in mapper.columns:
                sa_col_type = type(mapper.columns[col].type)                

            # Use options if provided for this column
            if options and col in options:
                col_options = options[col]
                select_options = [("None", None)] + list(col_options.items())
                current_idx = 0
                if val is not None:
                    for i, (_, obj) in enumerate(select_options):
                        if hasattr(obj, 'id') and hasattr(val, 'id'):
                            if obj.id == val.id:
                                current_idx = i
                        elif obj == val:
                            current_idx = i
                selected_label, selected_obj = st.selectbox(label, select_options, index=current_idx, format_func=lambda x: x[0])
                logging.info(f"Selected label: {selected_label}")
                logging.info(f"Selected obj: {selected_obj}")
                new_val = selected_obj

            # Create text area field if of SQLAlchemy type Text.
            elif sa_col_type == Text:
                new_val = st.text_area(label, value=val or "")
                if new_val == "":
                    new_val = None

            # Create text input field if of SQLAlchemy type String.
            elif sa_col_type == String:
                new_val = st.text_input(label, value=val or "")
                if new_val == "":
                    new_val = None

            # Create text input field if of SQLAlchemy type String.
            elif sa_col_type == Date:
                new_val = st.date_input(label, value=pd.to_datetime(val) if val else None, format="YYYY-MM-DD") 
                       
            # Create remaining form fields based on Python type.
            elif isinstance(val, int):
                new_val = st.number_input(label, value=val, step=1)
            elif isinstance(val, float):
                new_val = st.number_input(label, value=val, format="%f")
            else:
                # Fallback to string input
                new_val = st.text_input(label, value=str(val) if val is not None else "")
                if new_val == "":
                    new_val = None
            setattr(instance, col, new_val)

        # Create form buttons
        submitted = st.form_submit_button(button_label)
        cancel = st.form_submit_button("Cancel")
        if cancel:
            st.info("Edit cancelled.")
            return st.rerun()
        return submitted