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
    columns = ['title', 'parent_id', 'organization', 'project_manager', 'project_sponsor',
               'description', 'initiation_date', 'closure_date']
    submitted = create_form(project, columns, button_label="Add")
    if submitted:
        controller.add_project(project)
        st.rerun()

@st.dialog("Edit Project")                 
def edit_project():
    """
    Show a form to edit the selected project.
    """
    # Get the select row from session state.
    selected_row = st.session_state.get('selected_row', None)
    if selected_row is None:
        st.error("Please select a project to edit.")
        return
    # Parent project selector
    all_projects = controller.get_projects()
    parent_options = [("No parent", None)] + [
        (f"{p.title} (ID {p.project_id})", p.project_id)
        for p in all_projects if p.project_id != selected_row['project_id']
    ]
    # Find the current parent option index
    current_parent_id = selected_row.get('parent_id', None)
    if current_parent_id is None:
        parent_idx = 0
    else:
        parent_idx = next((i for i, (_, pid) in enumerate(parent_options) if pid == current_parent_id), 0)
    # Build edit form.
    with st.form("edit_project_form", clear_on_submit=False):
        st.subheader(f"Edit Project: {selected_row['title']} (ID {selected_row['project_id']})")
        # Form fields
        new_title = st.text_input("Title", value=selected_row['title'], max_chars=255)
        parent_label, new_parent_id = st.selectbox(
            "Parent project",
            parent_options,
            index=parent_idx,
            format_func=lambda x: x[0]
        )        
        new_organization = st.text_input("Organization", value=selected_row['organization'], max_chars=255)
        new_manager = st.text_input("Manager", value=selected_row['project_manager'], max_chars=255)
        new_sponsor = st.text_input("Sponsor", value=selected_row['project_sponsor'], max_chars=255)
        new_description = st.text_area("Description", value=selected_row['description'])
        new_initiation_date = st.date_input("Start date", value=pd.to_datetime(selected_row['initiation_date']) if selected_row['initiation_date'] else None, format="YYYY-MM-DD")
        new_closure_date = st.date_input("End date", value=pd.to_datetime(selected_row['closure_date']) if selected_row['closure_date'] else None, format="YYYY-MM-DD")
        # Form buttons
        submitted_edit = st.form_submit_button("Update")
        cancel_edit = st.form_submit_button("Cancel")
        # Form logic
        if submitted_edit:
            project = controller.get_project(int(selected_row['project_id']))
            if project is None:
                st.error("Project not found.")
                return
            project.title = new_title
            project.parent_id = new_parent_id
            project.organization = new_organization
            project.project_manager = new_manager
            project.project_sponsor = new_sponsor
            project.description = new_description
            project.initiation_date = new_initiation_date
            project.closure_date = new_closure_date
            controller.update_project(project)
            st.success("Project updated.")
            st.rerun()               
        elif cancel_edit:
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