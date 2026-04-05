"""
This module contains the code related to the milestones tab.
"""

import streamlit as st
from plog.common import create_form, create_table
from plog.models.milestone import Milestone
from plog.controllers.milestone_controller import MilestoneController


def milestones_table():
    """
    Show a table with all milestones for the current project.
    """
    # Get the SQLAlchemy session from Streamlit session state
    session = st.session_state['session']
    project = st.session_state['project']
    controller = MilestoneController(session)

    # Get all milestones for the current project from the database.
    milestones = controller.get_all(project=project)
    if not milestones:
        st.info("No Milestones found.")
        return

    # Define columns for display.
    columns = {
        'title': 'Title',
        'id': 'ID',
        'acceptance_criteria': 'Acceptance Criteria',
        'initial_baseline_date': 'Initial Baseline',
        'latest_baseline_date': 'Latest Baseline',
        'description': 'Description',
    }
    response = create_table(milestones, columns, parent_column='parent_id')

    # Get the selected row (if any).
    selected_rows = response.get('selected_rows', None)
    if selected_rows is not None:
        st.session_state['selected_row'] = selected_rows.iloc[0]


@st.dialog("Add Milestone")
def add_milestone():
    """
    Show a form to add a new milestone.
    """
    session = st.session_state['session']
    project = st.session_state['project']
    controller = MilestoneController(session)

    milestone = Milestone()
    milestone.project_id = project.id
    columns = {
        'title': 'Title',
        'parent_id': 'Parent',
        'acceptance_criteria': 'Acceptance Criteria',
        'initial_baseline_date': 'Initial Baseline',
        'description': 'Description',
    }
    options = {'parent_id': controller.possible_parents(milestone)}
    submitted = create_form(milestone, columns, options, button_label="Add")
    if submitted:
        milestone.project = project
        milestone.latest_baseline_date = milestone.initial_baseline_date
        controller.add(milestone)
        st.rerun()


@st.dialog("Edit Milestone")
def edit_milestone():
    """
    Show a form to edit an existing milestone.
    """
    session = st.session_state['session']
    project = st.session_state['project']
    controller = MilestoneController(session)

    # Get the selected row from session state.
    selected_row = st.session_state.get('selected_row', None)
    if selected_row is None:
        st.error("Please select a project to edit.")
        return
    milestone = controller.get_by_id(int(selected_row['id']))
    columns = {
        'title': 'Title',
        'parent_id': 'Parent',
        'acceptance_criteria': 'Acceptance Criteria',
        'initial_baseline_date': 'Initial Baseline',
        'latest_baseline_date': 'Latest Baseline',
        'description': 'Description',
    }
    options = {'parent_id': controller.possible_parents(milestone)}
    submitted = create_form(milestone, columns, options)
    if submitted:
        controller.update(milestone)
        st.rerun()


@st.dialog("Confirm Deletion")
def delete_milestone():
    """
    Delete the currently selected milestone after confirmation.
    """
    session = st.session_state['session']
    project = st.session_state['project']
    controller = MilestoneController(session)

    selected_row = st.session_state.get('selected_row', None)
    if selected_row is None:
        st.error("No project selected for deletion.")
        return
    # Show confirmation dialog
    st.warning(f"Are you sure you want to delete milestone '{selected_row['title']}' (ID {selected_row['id']})?")
    confirm = st.button("Yes, delete milestone", key="confirm_delete")
    cancel = st.button("Cancel", key="cancel_delete")
    if confirm:
        controller.delete_by_id(int(selected_row['id']))
        st.success("Project deleted.")
        del st.session_state['selected_row']
        st.rerun()
    elif cancel:
        st.info("Deletion cancelled.")
        st.rerun()