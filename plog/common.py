import atexit
import logging
import os
import pandas as pd
import streamlit as st

from datetime import date, datetime as dt
from sqlalchemy import create_engine, Date, String, Text
from sqlalchemy.orm import class_mapper, configure_mappers, sessionmaker
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
    
from plog.models.common import Base
from plog.models.milestone import Milestone
from plog.models.project import Project
from plog.controllers.project_controller import ProjectController


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



def create_table(objects, columns, parent_column=None):
    """
    Display a table of SQLAlchemy model instances using st_aggrid.

    :param instances: List of SQLAlchemy model instances to display.
    :type instances: list[object]
    :param columns: Dictionary mapping column names to labels for display.
    :type columns: dict[str, str]
    :param parent_column: Optional column name for hierarchical display.
    :type parent_column: str
    """
    
    def get_hierarchy_path(object, id_map):
        """
        Returns the full path from root to the object as a string.
        
        The path is a string of IDs separated by slashes, e.g. "1/2/3".
        
        :param object: SQLAlchemy model instance for which to get the path.
        :type object: object
        :param id_map: Dictionary mapping IDs to objects for parent traversal.
        :type id_map: dict[int, object]
        :returns: Path to the object.
        :rtype: str
        """
        path = []
        current = object
        while current is not None:
            path.append(str(current.id))
            current = id_map.get(current.parent_id)
        return '/'.join(reversed(path))

    # Build a lookup for parent traversal and add 'path' column if needed
    rows = []
    if parent_column is not None:
        id_map = {getattr(obj, 'id', None): obj for obj in objects}
        for obj in objects:
            row = {col: getattr(obj, col, None) for col in columns.keys()}
            row['path'] = get_hierarchy_path(obj, id_map)
            rows.append(row)
        df = pd.DataFrame(rows)
    else:
        df = pd.DataFrame([
            {col: getattr(obj, col, None) for col in columns.keys()} for obj in objects
        ])

    # Add preformatted date columns  .
    mapper = class_mapper(type(objects[0]))
    for col, label in columns.items():
        if type(mapper.columns[col].type) == Date:
            # Insert pre-formatted date column.
            fmt_col = f"{col}_formatted"
            df.insert(
                loc=df.columns.get_loc(col) + 1,
                column=fmt_col,
                value=df[col].apply(lambda d: d.strftime("%Y-%m-%d") if d is not None else "")
            )

    # Build grid options.
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(flex=1)
    gb.configure_selection('single')

    # Configure display of columns.
    for col, label in columns.items():
        if type(mapper.columns[col].type) == Date:
            # Configure display of preformatted date columns.            
            fmt_col = f"{col}_formatted"
            gb.configure_column(fmt_col, headerName=label)
            # Hide original date column.
            gb.configure_column(col, hide=True)                        
        else:
            gb.configure_column(col, headerName=label)

    # Configure display of hiararchy if parent_column was provided.
    if parent_column is not None:
        first_col, first_label = next(iter(columns.items()))
        gb.configure_grid_options(
            treeData=True,
            getDataPath=JsCode("function(data) { return data.path.split('/'); }"),
            autoGroupColumnDef={
                "headerName": first_label,
                "field": first_col,
                "cellRendererParams": {"suppressCount": True}
            },
            groupDefaultExpanded=-1,
            animateRows=True
        )
        gb.configure_column(first_col, hide=True)
        gb.configure_column('path', hide=True)
    grid_options = gb.build()

    # Show the grid
    response = AgGrid(
        df,
        gridOptions=grid_options,        
        update_mode='MODEL_CHANGED',
        fit_columns_on_grid_load=True,
        use_container_width=True,
        enable_enterprise_modules=True,
        allow_unsafe_jscode=True
    )
    return response

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

            # Create text input field if of SQLAlchemy type Date.
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


def create_sidebar(session=None):
    """
    Creates a streamlit sidebar with a project selection box and navigation sections.
    The sidebar is divided into a regular section and an admin section.

    :param session: SQLAlchemy session to use (optional, default: None).
    :type session: sqlalchemy.orm.Session
    """
    # Check if session is provided, otherwise use the one from session state
    if session is None:
        session = st.session_state['session']

    with st.sidebar:
        # Create project selection box.
        controller = ProjectController(session)
        projects = {p.id: p.title for p in controller.get_all()}
        index = 0
        if 'project' in st.session_state:
            project = st.session_state['project']
            index = list(projects.keys()).index(project.id)
        selected_id = st.selectbox(
            "Current project",
            projects,
            index=index,
            format_func=lambda id: f"{projects[id]} (ID {id})"
        )       
        if selected_id:
            project = controller.get_by_id(selected_id)
            st.session_state['project'] = project
            logging.info(f"Project '{project.title} (ID {project.id})' selected as current project.")
              
        # Define navigation menu.
        pages = {
            'Project': [
                st.Page("pages/milestones.py", title="Milestones")
            ],
            'Admin': [
                st.Page("pages/projects.py", title="Projects")
            ]              
        }
        page = st.navigation(pages)
       
    # Disply the current page.
    page.run()
        