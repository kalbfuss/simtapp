import logging
import os
import streamlit as st

from datetime import date, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import configure_mappers, sessionmaker

from plog.models.project import Project, Base
from plog.controllers.project_controller import ProjectController


# Enable debug level logging
logging.basicConfig(level=logging.DEBUG)

# Create database and session
db_path = os.path.abspath("plog.sqlite")
configure_mappers()
engine = create_engine(f'sqlite:///{db_path}')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

# Create instance of controller we want to test
controller = ProjectController(session)

#st.title("Main Page")
#st.write("Welcome to the main page of the Streamlit app!")