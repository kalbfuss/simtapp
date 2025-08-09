"""
This page displays all projects in the database using streamlit-aggrid.
All code and documentation must be in English.
"""

import pandas as pd
import streamlit as st

from plog.common import init, create_form, parse_date
from plog.models.project import Project
from plog.controllers.project_controller import ProjectController

from st_aggrid import AgGrid, GridOptionsBuilder, JsCode


# Initialize the application.
init()

# Get the SQLAlchemy session from Streamlit session state
session = st.session_state['session']
controller = ProjectController(session)

def projects_table():
    """
    Display projects in a table.
    """
    projects = controller.get_projects()
    if projects is None:
        st.info("No projects found.")
        return
    # Build a lookup for parent traversal.
    id_map = {p.project_id: p for p in projects}
    def get_hierarchy_path(proj):
        # Returns the full path from root to the given project as a string
        path = []
        current = proj
        while current is not None:
            path.append(str(current.project_id))
            current = id_map.get(current.parent_id)
        return '/'.join(reversed(path))
    # Build panda data frame.
    df = pd.DataFrame([
        {
            'project_id': p.project_id,
            'title': p.title,
            'organization': p.organization,
            'project_manager': p.project_manager,
            'project_sponsor': p.project_sponsor,
            'initiation_date': p.initiation_date,
            'closure_date': p.closure_date,
            'description': p.description,
            'parent_id': p.parent_id,
            'path': get_hierarchy_path(p)
        }
        for p in projects
    ])
    # Build grid options.
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(flex=1)
    gb.configure_selection('single')
    gb.configure_grid_options(
        treeData=True,
        getDataPath=JsCode("function(data) { return data.path.split('/'); }"),
        autoGroupColumnDef={
            "headerName": "Path",
            "field": "title",
            "minWidth": 300,
            "cellRendererParams": {"suppressCount": True}
        },
        groupDefaultExpanded=-1,
        animateRows=True
    )
    grid_options = gb.build()
    # Show the grid.
    grid_response = AgGrid(
        df,
        gridOptions=grid_options,
        update_mode='MODEL_CHANGED',
        fit_columns_on_grid_load=True,
        use_container_width=True,
        enable_enterprise_modules=True,
        allow_unsafe_jscode=True,
    )
    # Get the selected row (if any).
    selected_rows = grid_response.get('selected_rows', None)
    if selected_rows is not None:
        st.session_state['selected_row'] = selected_rows.iloc[0]

@st.dialog("Add Project")
def add_project():
    """
    Show a form to add a new project.
    """
    project = Project()
    columns = {
        'title': 'Title',
        'parent_id': 'Parent',
        'organization': 'Organization',
        'project_manager': 'Project Manager',
        'project_sponsor': 'Project Sponsor',
        'description': 'Description',
        'initiation_date': 'Initiation Date',
        'closure_date': 'Closure Date'
    }
    options = { 'parent_id': controller.possible_parents()}
    submitted = create_form(project, columns, options, button_label="Add")
    if submitted:
        controller.add_project(project)
        st.rerun()

@st.dialog("Edit Project")
def edit_project():
    """
    Show a form to edit an existing project.
    """
    # Get the select row from session state.
    selected_row = st.session_state.get('selected_row', None)
    if selected_row is None:
        st.error("Please select a project to edit.")
        return
    project = controller.get_project(int(selected_row['project_id']))
    columns = {
        'title': 'Title',
        'parent_id': 'Parent',
        'organization': 'Organization',
        'project_manager': 'Project Manager',
        'project_sponsor': 'Project Sponsor',
        'description': 'Description',
        'initiation_date': 'Initiation Date',
        'closure_date': 'Closure Date'
    }
    options = { 'parent_id': controller.possible_parents(project)}
    submitted = create_form(project, columns, options)
    if submitted:
        controller.add_project(project)
        st.rerun()

@st.dialog("Confirm Deletion")
def delete_project():
    """
    Delete the currently selected project after confirmation.
    """
    selected_row = st.session_state.get('selected_row', None)
    if selected_row is None:
        st.error("No project selected for deletion.")
        return
    # Show confirmation dialog
    st.warning(f"Are you sure you want to delete project '{selected_row['title']}' (ID {selected_row['project_id']})?")
    confirm = st.button("Yes, delete project", key="confirm_delete")
    cancel = st.button("Cancel", key="cancel_delete")
    if confirm:
        controller.delete_by_id(int(selected_row['project_id']))
        st.success("Project deleted.")
        del st.session_state['selected_row']
        st.rerun()
    elif cancel:
        st.info("Deletion cancelled.")
        st.rerun()

# Start page code.
st.set_page_config(layout="wide")
st.title("Projects")
st.write("This page allows you to manage all projects within your database.")

projects_table()
add_clicked = st.button("Add")
edit_clicked = st.button("Edit")
delete_clicked = st.button("Delete")

if add_clicked:
    add_project()
if edit_clicked:
    edit_project()    
if delete_clicked:
    delete_project()