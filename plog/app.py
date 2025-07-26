import logging
import os
import streamlit as st

from datetime import date, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import configure_mappers, sessionmaker

from plog.models.project import Project, Base
from plog.controllers.project_controller import ProjectController
from plog.controllers.milestone_controller import MilestoneController


# Enable debug level logging
logging.basicConfig(level=logging.DEBUG)

# Create database and session
db_path = os.path.abspath("test_projects.sqlite")
if os.path.exists(self.db_path):
    os.remove(self.db_path)
configure_mappers()
engine = create_engine(f'sqlite:///{self.db_path}')
Base.metadata.create_all(self.engine)
Session = sessionmaker(bind=self.engine)
session = Session()

# Create instance of controller we want to test
controller = ProjectController(self.session)

st.title("Main Page")
st.write("Welcome to the main page of the Streamlit app!")